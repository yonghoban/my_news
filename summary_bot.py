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

target_channels = ['@cookiesreads', '@somoreads', '@iansintel', '@icodrops']
my_channel_username = '@turtleking11' 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# 1. 링크 내용 가져오기
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

# 2. Gemini AI 분석
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

# 3. 개인 메시지 처리
async def process_private_messages(client, bot_username, my_channel_id):
    print(f"📩 @gangjaa님이 {bot_username}에게 보낸 메시지 확인 중...")
    # 넉넉하게 4시간 전 메시지까지 확인 (혹시 봇이 오래 죽었을 때를 대비)
    check_limit = datetime.now(timezone.utc) - timedelta(hours=4) 
    
    async for msg in client.iter_messages(bot_username, limit=20):
        if msg.date < check_limit: break
        
        if msg.out and msg.text:
            # [중복 방지] 이미 봇이 처리했는지 확인 (답장이 있으면 처리된 것)
            # 여기서는 간단히 구현하지만, 원한다면 내 채널에 검색 로직 추가 가능
            
            print(f"📝 메시지 발견: {msg.text[:15]}...")
            
            urls = re.findall(r'(https?://\S+)', msg.text)
            if urls:
                content = fetch_content(urls[0])
                if content:
                    summary = ai_analyze(content, url_type="article")
                    source_info = f"🔗 **원본 링크:** {urls[0]}"
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
            
            await bot.send_message(my_channel_id, report_msg)
            await bot.send_message(msg.chat_id, "✅ 분석 완료! 채널을 확인하세요.")
            await asyncio.sleep(5)

# 4. [핵심 기능] 이미 게시된 링크인지 확인하는 함수
async def get_posted_urls(bot, channel_id):
    print("🧹 중복 방지를 위해 최근 게시물 확인 중...")
    posted_urls = set()
    # 내 채널의 최근 50개 메시지를 확인해서 이미 올린 URL 수집
    async for msg in bot.iter_messages(channel_id, limit=50):
        if msg.text:
            urls = re.findall(r'(https?://\S+)', msg.text)
            if urls:
                posted_urls.add(urls[0]) # 메시지에 포함된 첫 번째 링크 저장
    return posted_urls

# 5. 메인 실행
async def main():
    print("🧠 심층 분석 봇 가동 (스마트 중복 방지 모드)...")
    await client.start()
    await bot.start(bot_token=bot_token)
    
    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
        bot_user = await bot.get_me()
        bot_username = bot_user.username
    except Exception as e:
        print(f"❌ 설정 오류: {e}")
        return

    # 1. 개인 메시지 처리
    try:
        await process_private_messages(client, bot_username, my_channel_id)
    except Exception as e:
        print(f"⚠️ 개인 메시지 처리 중: {e}")

    # 2. [스마트 중복 방지] 내 채널에 이미 올린 링크 목록 가져오기
    posted_urls = await get_posted_urls(bot, my_channel_id)
    print(f"🛡️ 이미 처리된 링크 {len(posted_urls)}개 제외 예정")

    # 3. 채널 스캔 (시간 범위 대폭 확대: 4시간)
    # 봇이 3시간 동안 죽어있어도, 4시간 전 글까지 훑으므로 놓치는 게 없음
    chk_time = 14400 # 4시간 (1시간 아님!)
    
    for channel in target_channels:
        print(f"📡 {channel} 스캔 중...")
        try:
            async for msg in client.iter_messages(channel, limit=15):
                # 4시간보다 오래된 건 무시
                if (datetime.now(timezone.utc) - msg.date).total_seconds() > chk_time: continue
                
                text = msg.message if msg.message else ""
                urls = re.findall(r'(https?://\S+)', text)
                
                if urls:
                    target_url = urls[0]
                    
                    # [핵심] 이미 내 채널에 올린 링크면 분석하지 않고 건너뜀
                    if target_url in posted_urls:
                        print(f"⏩ 스킵 (이미 분석함): {target_url}")
                        continue
                    
                    # 새로운 링크면 분석 시작
                    content = fetch_content(target_url)
                    if not content: content = text
                    
                    await asyncio.sleep(5) 
                    summary = ai_analyze(content)
                    
                    final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({target_url})\n출처: {channel}"
                    await bot.send_message(my_channel_id, final_msg, link_preview=False)
                    
                    # 방금 올린 것도 중복 목록에 추가 (한 번의 실행 주기 내 중복 방지)
                    posted_urls.add(target_url)

        except Exception as e:
            print(f"⚠️ {channel} 에러: {e}")
            continue

with client:
    client.loop.run_until_complete(main())
