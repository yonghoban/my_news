import os
import asyncio
import re
import requests
import google.generativeai as genai
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone

# === [설정 영역: 깃허브 Secrets에서 가져옴] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

# 1. 분석할 대상 채널 (영어 뉴스/트윗이 올라오는 곳)
# 여기에 감시하고 싶은 채널들을 계속 추가하세요.
target_channels = [
    '@VitalikButerin', 
    '@BanklessHQ',
    '@Tree_of_Alpha',
    '@tier10k',
    '@unusual_whales'
]

# 2. [수정됨] 결과물을 받아볼 내 새 채널
my_channel_username = '@turtleking11' 

# === [AI 설정] ===
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# === [핵심 기능 1: 링크 내용 읽어오기 (Jina AI)] ===
def fetch_content(url):
    print(f"🔍 링크 읽기 시도: {url}")
    try:
        # Jina Reader API (무료)
        reader_url = f"https://r.jina.ai/{url}"
        headers = {
            'X-Return-Format': 'markdown',
            'X-With-Generated-Alt': 'true'
        }
        response = requests.get(reader_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            text = response.text
            # 차단되었거나 내용이 너무 짧으면 실패 처리
            if "Access Denied" in text or len(text) < 50:
                return None
            return text[:6000] # Gemini 입력 한계 고려
        else:
            return None
    except Exception as e:
        print(f"❌ 에러: {e}")
        return None

# === [핵심 기능 2: AI 번역 및 요약] ===
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
    - (Translate technical terms to Korean)

    **3. 시장 영향 (Impact)**
    - (Positive/Negative/Neutral and why)

    [Source Content]
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 분석 실패: {e}"

async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)

    # 내 새 채널 ID 찾기 (@turtleking11)
    try:
        entity = await client.get_entity(my_channel_username)
        # 채널 ID는 보통 -100으로 시작합니다.
        my_channel_id = int(f"-100{entity.id}")
        print(f"✅ 전송 타겟: {my_channel_username} (ID: {my_channel_id})")
    except Exception as e:
        print(f"❌ 채널을 찾을 수 없습니다: {e}")
        print("💡 봇이 해당 채널에 관리자로 들어가 있는지 확인해주세요!")
        return

    # 최근 1시간(3600초) 내의 메시지만 확인
    chk_time = 3600 

    for channel in target_channels:
        try:
            print(f"📡 스캔 중: {channel}")
            # 너무 많이 읽으면 느려지니 최근 5개만 확인
            async for msg in client.iter_messages(channel, limit=5):
                # 시간 체크
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > chk_time: continue

                text = msg.message if msg.message else ""
                
                # 링크 추출
                urls = re.findall(r'(https?://\S+)', text)
                if not urls: continue 

                target_url = urls[0]
                
                # 1. 내용 읽기 (Scraping)
                content = fetch_content(target_url)
                
                # 2. 내용 없으면 텔레그램 본문 사용
                if not content:
                    print("⚠️ 원문 읽기 실패 -> 메시지 본문으로 분석")
                    content = text 
                    url_type = "short_text"
                else:
                    url_type = "article"

                # 3. AI 분석
                print("🤖 AI 분석 중...")
                summary = ai_analyze(content, url_type)

                # 4. @turtleking11 채널로 전송
                final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본 링크]({target_url})\n출처: {channel}"
                
                await bot.send_message(my_channel_id, final_msg, link_preview=False)
                print(f"✅ 전송 완료: {target_url}")

        except Exception as e:
            print(f"에러 ({channel}): {e}")

with client:
    client.loop.run_until_complete(main())
