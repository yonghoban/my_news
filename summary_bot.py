import os
import asyncio
import re
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone, timedelta
from google import genai  # [NEW] 최신 라이브러리

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

# 감시할 채널
target_channels = [
    '@cookiesreads',
    '@somoreads'
]

# 결과 받을 채널
my_channel_username = '@turtleking11' 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# [NEW] 최신 Gemini 클라이언트 설정
ai_client = genai.Client(api_key=gemini_api_key)

# 1. Jina AI로 내용 읽기
def fetch_content(url):
    print(f"🔍 링크 읽기 시도: {url}")
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {'X-Return-Format': 'markdown', 'X-With-Generated-Alt': 'true'}
        response = requests.get(reader_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            if "Access Denied" in text or len(text) < 50: return None
            return text[:6000]
        return None
    except Exception as e:
        print(f"❌ 읽기 에러: {e}")
        return None

# 2. AI 분석 (최신 라이브러리 사용)
def ai_analyze(text, url_type="article"):
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
    
    try:
        # [NEW] google-genai 최신 호출 방식
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"⚠️ AI 분석 실패: {e}"

async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)

    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
        print(f"✅ 전송 타겟: {my_channel_username} (ID: {my_channel_id})")
    except Exception as e:
        print(f"❌ 채널 찾기 실패: {e}")
        return

    # 24시간 이내 글 확인
    chk_time = 86400 

    for channel in target_channels:
        try:
            print(f"📡 스캔 중: {channel}")
            # 최근 10개 확인
            async for msg in client.iter_messages(channel, limit=10):
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > chk_time: continue

                text = msg.message if msg.message else ""
                urls = re.findall(r'(https?://\S+)', text)
                if not urls: continue 

                target_url = urls[0]
                
                # 내용 읽기
                content = fetch_content(target_url)
                if not content:
                    print("⚠️ 원문 읽기 실패 -> 메시지 본문 사용")
                    content = text 
                    url_type = "short_text"
                else:
                    url_type = "article"

                # AI 분석
                print("🤖 AI 분석 중...")
                summary = ai_analyze(content, url_type)

                # 전송
                final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본 링크]({target_url})\n출처: {channel}"
                await bot.send_message(my_channel_id, final_msg, link_preview=False)
                print(f"✅ 전송 완료: {target_url}")

        except Exception as e:
            print(f"에러 ({channel}): {e}")

with client:
    client.loop.run_until_complete(main())
