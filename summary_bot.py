import os, asyncio, re, requests, json, time
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone, timedelta

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

# 1. Jina AI를 통한 웹 페이지 내용 추출
def fetch_content(url):
    print(f"🔍 링크 읽기 시도: {url}")
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {'X-Return-Format': 'markdown', 'X-With-Generated-Alt': 'true'}
        response = requests.get(reader_url, headers=headers, timeout=20)
        if response.status_code == 200:
            text = response.text
            if "Access Denied" in text or len(text) < 50: return None
            return text[:6000] # 분석 가능한 길이로 제한
        return None
    except:
        return None

# 2. Gemini AI 분석 (성공했던 모델 구성 적용)
def ai_analyze(text, url_type="article"):
    # 1순위: 2.0 Flash Lite (가장 안정적), 2순위: 2.5 Flash
    models = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-flash-lite-latest"]
    
    prompt = f"""
    You are a crypto market intelligence expert. 
    Analyze the following content and provide a structured summary in Korean.
    [Output Format]
    **1. 한줄 요약 (Headline)**
    - (Catchy title)
    **2. 핵심 내용 (Key Points)**
    - (Max 3 points)
    **3. 인사이트 (Insight)**
    - (Market implication)

    [Source Content]
    {text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    for model_name in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api_key}"
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                time.sleep(3) # 과부하 방지
                continue
        except:
            continue
    return "⚠️ 분석 실패 (AI 모델 응답 없음)"

# 3. 개인 메시지(텍스트 및 URL) 복습 및 분석
async def process_private_messages(bot, my_channel_id):
    print("📩 개인 요청 확인 중...")
    check_limit = datetime.now(timezone.utc) - timedelta(hours=1, minutes=10)
    
    async for msg in bot.iter_messages(None):
        if msg.date < check_limit: break
        if msg.is_private and msg.text and not msg.out:
            urls = re.findall(r'(https?://\S+)', msg.text)
            if urls:
                # URL이 포함된 경우 링크 접속 시도
                target_url = urls[0]
                content = fetch_content(target_url)
                if content:
                    summary = ai_analyze(content, url_type="article")
                    source_info = f"🔗 **원본 링크:** {target_url}"
                else:
                    summary = ai_analyze(msg.text, url_type="short_text")
                    source_info = "⚠️ (사이트 접속 실패로 보낸 텍스트만 분석함)"
            else:
                # 텍스트만 있는 경우
                summary = ai_analyze(msg.text, url_type="short_text")
                source_info = "📝 직접 입력한 텍스트"

            original_preview = msg.text if len(msg.text) < 150 else msg.text[:150] + "..."
            report_msg = (
                f"📥 **[Personal Request Report]**\n\n"
                f"💬 **원본 내용:**\n"
                f"> {original_preview}\n\n"
                f"{source_info}\n"
                f"--- AI 분석 결과 ---\n"
                f"{summary}"
            )
            await bot.send_message(my_channel_id, report_msg)
            await msg.reply("✅ 분석이 완료되어 채널에 게시되었습니다.")
            await asyncio.sleep(5)

# 4. 메인 실행 로직
async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)
    
    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
    except: return

    # 개인 메시지 먼저 처리
    await process_private_messages(bot, my_channel_id)

    # 채널 스캔 (최근 1시간 이내)
    chk_time = 3600
    for channel in target_channels:
        async for msg in client.iter_messages(channel, limit=10):
            if (datetime.now(timezone.utc) - msg.date).total_seconds() > chk_time: continue
            text = msg.message if msg.message else ""
            urls = re.findall(r'(https?://\S+)', text)
            if urls:
                content = fetch_content(urls[0])
                if not content: content = text
                await asyncio.sleep(5)
                summary = ai_analyze(content)
                final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({urls[0]})\n출처: {channel}"
                await bot.send_message(my_channel_id, final_msg, link_preview=False)

with client:
    client.loop.run_until_complete(main())
