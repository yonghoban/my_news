import os
import asyncio
import re
import requests
import json
import time
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

target_channels = ['@cookiesreads', '@somoreads']
my_channel_username = '@turtleking11' 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

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

# [핵심 수정] 사용자 JSON 목록에 있는 '정확한 이름'만 사용
def ai_analyze(text, url_type="article"):
    # 1순위: 2.0 Flash Lite (무료 티어에서 가장 확률 높음)
    # 2순위: Flash Latest (자동 연결)
    # 3순위: Pro Latest (Flash가 막혔을 때 대안)
    models_to_try = [
        "gemini-2.0-flash-lite", 
        "gemini-flash-latest",
        "gemini-pro-latest"
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

    error_logs = [] # 모든 에러를 기록

    for model_name in models_to_try:
        try:
            print(f"🤖 모델 시도: {model_name}...")
            # v1beta 사용 (최신 모델용)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            elif response.status_code == 429:
                # 사용량 초과 시 3초 대기 후 다음 모델
                msg = f"⚠️ {model_name}: 429 (Quota Exceeded)"
                print(msg)
                error_logs.append(msg)
                time.sleep(3)
                continue
            
            else:
                # 그 외 에러 (404 등)
                msg = f"⚠️ {model_name}: {response.status_code} ({response.text[:50]}...)"
                print(msg)
                error_logs.append(msg)
                continue
                
        except Exception as e:
            msg = f"⚠️ {model_name} Error: {str(e)}"
            error_logs.append(msg)
            continue

    # 3개 다 실패하면 실패 사유 리스트를 전송
    error_summary = "\n".join(error_logs)
    return f"⚠️ 분석 실패 (모든 모델 오류)\n\n[에러 로그]\n{error_summary}"

async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)

    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
    except:
        return

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

                # 429 방지 대기
                print("⏳ 5초 대기...")
                time.sleep(5)

                summary = ai_analyze(content)

                final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({target_url})\n출처: {channel}"
                await bot.send_message(my_channel_id, final_msg, link_preview=False)
                print(f"✅ 완료: {target_url}")

        except Exception as e:
            print(f"에러: {e}")

with client:
    client.loop.run_until_complete(main())
