import os
import asyncio
import re
import requests
import json
import time # [추가] 시간 지연을 위해 필요
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

# 감시할 채널
target_channels = ['@cookiesreads', '@somoreads']
my_channel_username = '@turtleking11' 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# 1. Jina AI 읽기
def fetch_content(url):
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {'X-Return-Format': 'markdown', 'X-With-Generated-Alt': 'true'}
        response = requests.get(reader_url, headers=headers, timeout=20)
        if response.status_code == 200:
            text = response.text
            if "Access Denied" in text or len(text) < 50: return None
            return text[:6000]
        return None
    except:
        return None

# 2. [수정됨] AI 분석 (무료 티어 호환성 강화)
def ai_analyze(text, url_type="article"):
    # 시도할 모델 순서 (무료 티어에서 확실한 것부터)
    # gemini-flash-latest: 현재 사용 가능한 최신 무료 Flash 모델로 자동 연결됨
    models = [
        "gemini-flash-latest", 
        "gemini-pro",
        "gemini-1.5-flash-latest"
    ]
    
    prompt = f"""
    You are a crypto market intelligence expert.
    Analyze the following content and provide a structured summary in Korean.

    [Content Type]: {url_type}

    [Output Format]
    **1. 한줄 요약 (Headline)**
    - (Write a catchy, accurate title in Korean)

    **2. 핵심 내용 (Key Points)**
    - (Bullet points, 3 lines max)
    - (Translate technical terms to Korean naturally)

    **3. 인사이트 (Insight)**
    - (What is the implication for the crypto market? Positive/Negative/Neutral)

    [Source Content]
    {text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    for model_name in models:
        try:
            print(f"🤖 모델 시도 중: {model_name}...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                print(f"⚠️ {model_name} 사용량 초과 (429). 다음 모델 시도...")
                time.sleep(2) # 2초 대기 후 다음 모델
                continue
            else:
                print(f"⚠️ {model_name} 실패 ({response.status_code}).")
                continue
                
        except Exception as e:
            print(f"⚠️ 연결 실패: {e}")
            continue

    return "⚠️ 모든 AI 모델 분석 실패 (API 권한 또는 사용량 문제)"

async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)

    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
    except:
        return

    # 24시간 이내 글 확인
    chk_time = 86400 

    for channel in target_channels:
        try:
            print(f"📡 스캔 중: {channel}")
            async for msg in client.iter_messages(channel, limit=10):
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > chk_time: continue

                text = msg.message if msg.message else ""
                urls = re.findall(r'(https?://\S+)', text)
                if not urls: continue 

                target_url = urls[0]
                content = fetch_content(target_url)
                if not content: content = text 

                # [중요] 429 에러 방지를 위해 5초 대기 (무료 티어는 분당 요청 제한이 있음)
                print("⏳ AI 과부하 방지를 위해 5초 대기중...")
                time.sleep(5)

                summary = ai_analyze(content)

                final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({target_url})\n출처: {channel}"
                await bot.send_message(my_channel_id, final_msg, link_preview=False)
                print(f"✅ 완료: {target_url}")

        except Exception as e:
            print(f"에러: {e}")

with client:
    client.loop.run_until_complete(main())
