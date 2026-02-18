import os
import asyncio
import re
import requests
import json
import time
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone, timedelta

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

# 감시할 채널 리스트 (4개)
target_channels = ['@cookiesreads', '@somoreads', '@iansintel', '@icodrops']
# 리포트가 올라갈 내 채널
my_channel_username = '@turtleking11' 

# 클라이언트 초기화
client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# 1. 링크 내용 가져오기 (Jina AI)
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
    except:
        return None

# 2. Gemini AI 분석 (가격/리스크 분석 포함)
def ai_analyze(text, url_type="article"):
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
                time.sleep(3)
                continue
        except:
            continue
    return "⚠️ 분석 실패"

# 3. [핵심] 개인 메시지 처리 (Client 권한 사용)
# 사용자(@gangjaa)가 봇에게 보낸 메시지를 '사용자 계정'으로 접속해서 확인합니다.
async def process_private_messages(client, bot_username, my_channel_id):
    print(f"📩 @gangjaa님이 {bot_username}에게 보낸 메시지 확인 중...")
    check_limit = datetime.now(timezone.utc) - timedelta(hours=1, minutes=10)
    
    # 내(Client)가 봇과 나눈 대화방을 조회
    async for msg in client.iter_messages(bot_username, limit=10):
        if msg.date < check_limit: break
        
        # msg.out = True (내가 보낸 메시지), msg.text 존재 확인
        if msg.out and msg.text:
            print(f"📝 메시지 발견: {msg.text[:15]}...")
            
            # URL 포함 여부 확인
            urls = re.findall(r'(https?://\S+)', msg.text)
            if urls:
                target_url = urls[0]
                content = fetch_content(target_url)
                if content:
                    summary = ai_analyze(content, url_type="article")
                    source_info = f"🔗 **원본 링크:** {target_url}"
                else:
                    summary = ai_analyze(msg.text, url_type="short_text")
                    source_info = "⚠️ (사이트 접속 실패로 텍스트만 분석함)"
            else:
                summary = ai_analyze(msg.text, url_type="short_text")
                source_info = "📝 직접 입력한 텍스트"

            report_msg = (
                f"📥 **[Personal Request Report]**\n\n"
                f"💬 **원본:**\n> {msg.text[:100]}...\n\n"
                f"{source_info}\n---\n{summary}"
            )
            
            # 결과는 봇이 채널에 전송
            await bot.send_message(my_channel_id, report_msg)
            # 봇이 나에게 답장 (확인용)
            await bot.send_message(msg.chat_id, "✅ 분석 완료! 채널을 확인하세요.")
            
            await asyncio.sleep(5)

# 4. 메인 실행 로직
async def main():
    print("🧠 심층 분석 봇 가동...")
    await client.start()
    await bot.start(bot_token=bot_token)
    
    try:
        # 내 채널 ID 찾기
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
        
        # 봇의 Username 알아내기 (자동 감지)
        bot_user = await bot.get_me()
        bot_username = bot_user.username
    except Exception as e:
        print(f"❌ 초기 설정 오류: {e}")
        return

    # 1. 개인 메시지 처리 (Client 모드로 실행하여 에러 방지)
    try:
        await process_private_messages(client, bot_username, my_channel_id)
    except Exception as e:
        print(f"⚠️ 개인 메시지 처리 중 경고: {e}")

    # 2. 채널 스캔 (4개 채널)
    chk_time = 3600
    for channel in target_channels:
        print(f"📡 {channel} 스캔 중...")
        try:
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
        except Exception as e:
            print(f"⚠️ {channel} 스캔 중 에러 (건너뜀): {e}")
            continue

with client:
    client.loop.run_until_complete(main())
