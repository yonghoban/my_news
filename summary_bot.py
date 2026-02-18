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

# 2. [핵심 수정] AI 분석 (Lite 모델 우선 사용 + 에러 상세 출력)
def ai_analyze(text, url_type="article"):
    # 사용자 목록에 있던 모델들 중 '무료 가능성'이 높은 순서
    models = [
        "gemini-2.0-flash-lite",       # 1순위: 2.0 경량화 버전 (가장 유력)
        "gemini-2.0-flash-lite-preview-02-05", # 2순위: 프리뷰 버전
        "gemini-flash-latest",         # 3순위: 자동 연결 (보통 1.5로 연결됨)
        "gemini-1.5-flash",            # 4순위: 구형 안정 버전
        "gemini-1.5-flash-8b"          # 5순위: 초경량 버전
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

    last_error_msg = ""

    for model_name in models:
        try:
            print(f"🤖 모델 시도 중: {model_name}...")
            # 2.0 모델은 v1beta 사용
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
            
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                print(f"⚠️ {model_name} 사용량 초과 (429).")
                last_error_msg = f"{model_name}: Quota Exceeded (429)"
                time.sleep(2) 
                continue
            elif response.status_code == 404:
                print(f"⚠️ {model_name} 모델 없음 (404).")
                last_error_msg = f"{model_name}: Not Found (404)"
                continue
            else:
                error_detail = response.text[:200] # 에러 내용 일부 추출
                print(f"⚠️ {model_name} 실패 ({response.status_code}): {error_detail}")
                last_error_msg = f"{model_name} Error: {response.status_code} - {error_detail}"
                continue
                
        except Exception as e:
            last_error_msg = f"Connection Error: {str(e)}"
            continue

    # 모든 시도가 실패하면 텔레그램으로 에러 내용 전송
    return f"⚠️ 모든 AI 모델 분석 실패.\n마지막 에러: {last_error_msg}\n(API 키 결제 설정 확인이 필요할 수 있습니다)"

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

                # 과부하 방지 대기
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
