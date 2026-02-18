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

# [핵심 수정] 가격 범위 및 리스크 분석 프롬프트 고도화
def ai_analyze(text, url_type="article"):
    # 사용자 계정에서 가용한 최신 모델 리스트
    models = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-flash-lite-latest"]
    
    prompt = f"""
    You are a senior crypto investment analyst. 
    Analyze the following content based on fact-based and quantitative principles.

    [Output Format]
    **1. 한줄 요약 (Headline)**
    - 핵심 사건 중심의 간결하고 직설적인 요약

    **2. 핵심 내용 (Key Points)**
    - 주요 사실 관계 3가지 이내 (수치, 통계 등 정량 데이터 우선 기술)

    **3. 시장 영향 및 예상 가격 범위 (Price Impact & Range)**
    - 뉴스의 파급력을 바탕으로 한 단기 예상 변동성(%) 및 주요 지지/저항 가격대 추정
    - 일반 뉴스인 경우 시장 심리(Bullish/Bearish) 및 자금 흐름에 미치는 영향 분석

    **4. 위험 요소 및 보안 취약점 (Risk Factors)**
    - **DeFi/신규 프로젝트 필수**: 스마트 컨트랙트 감사 여부, 유동성 집중도, 팀 익명성 등 분석
    - 일반 뉴스의 경우 잠재적 하방 리스크 및 예외 상황(Edge cases) 기술

    **5. 최종 인사이트 (Insight)**
    - 2차 효과(Second-order effects) 및 투자 전략적 제언

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
                time.sleep(3) # Rate limit 방어
                continue
        except:
            continue
    return "⚠️ 분석 실패"

async def process_private_messages(bot, my_channel_id):
    check_limit = datetime.now(timezone.utc) - timedelta(hours=1, minutes=10)
    async for msg in bot.iter_messages(None):
        if msg.date < check_limit: break
        if msg.is_private and msg.text and not msg.out:
            urls = re.findall(r'(https?://\S+)', msg.text)
            if urls:
                content = fetch_content(urls[0])
                summary = ai_analyze(content if content else msg.text)
                source_info = f"🔗 **원본 링크:** {urls[0]}"
            else:
                summary = ai_analyze(msg.text)
                source_info = "📝 텍스트 요청"

            report_msg = (
                f"📥 **[Personal Request Report]**\n\n"
                f"💬 **원본:**\n> {msg.text[:100]}...\n\n"
                f"{source_info}\n---\n{summary}"
            )
            await bot.send_message(my_channel_id, report_msg)
            await msg.reply("✅ 분석 완료")
            await asyncio.sleep(5)

async def main():
    await client.start(); await bot.start(bot_token=bot_token)
    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
    except: return
    await process_private_messages(bot, my_channel_id)
    chk_time = 3600
    for channel in target_channels:
        async for msg in client.iter_messages(channel, limit=10):
            if (datetime.now(timezone.utc) - msg.date).total_seconds() > chk_time: continue
            urls = re.findall(r'(https?://\S+)', msg.message if msg.message else "")
            if urls:
                content = fetch_content(urls[0])
                summary = ai_analyze(content if content else msg.message)
                await bot.send_message(my_channel_id, f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({urls[0]})")
                await asyncio.sleep(5)

with client:
    client.loop.run_until_complete(main())
