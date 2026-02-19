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

# 1. 링크 내용 추출 (FxTwitter 및 Jina AI 이중 파이프라인)
def fetch_content(url):
    print(f"🔍 링크 파싱 시도: {url}")
    
    # [분기 1] 트위터 우회 라우팅 (FxTwitter API)
    if "twitter.com" in url or "x.com" in url:
        api_url = re.sub(r'(https?://)?(www\.)?(twitter\.com|x\.com)', 'https://api.fxtwitter.com', url)
        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and 'tweet' in data:
                    author = data['tweet'].get('author', {}).get('name', 'Unknown')
                    tweet_text = data['tweet'].get('text', '')
                    
                    if not tweet_text:
                        return f"[Twitter Post by {author}]\n(텍스트 없음 - 미디어/이미지 전용 트윗)"
                    
                    return f"[Twitter Post by {author}]\n{tweet_text}"[:6000]
            return None
        except Exception as e:
            print(f"⚠️ 트위터 API 추출 실패: {e}")
            return None

    # [분기 2] 일반 웹사이트 파싱 (Jina AI)
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

# 2. Gemini AI 분석 (인과관계 및 구조적 설명 모델 적용)
def ai_analyze(text, url_type="article"):
    models = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-flash-lite-latest"]
    
    prompt = f"""
    You are a strictly objective and logical crypto analyst.
    Your goal is to explain complex crypto news logically and easily, focusing on causality, first principles, and second-order effects.
    
    [Rules]
    1. Output STRICTLY in Korean.
    2. Eliminate all subjective adjectives. Use only facts, quantitative data, and logical deductions.
    3. End all sentences with noun forms (명사형 종결 - 예: ~함, ~임, ~상태).
    4. Separate verifiable facts from analytical implications.
    5. Explain complex concepts (e.g., Tokenomics, DeFi mechanisms) so that beginners can understand the structural cause.

    [Output Format]
    ### 1. 사건 개요 및 작동 원리 (Event & Mechanism)
    * **발생 현상 (Fact)**: (핵심 사건과 정량적 변화 수치 기술)
    * **발생 원리 (Causality)**: (해당 사건이 발생한 근본 원인과 시스템적 작동 원리를 쉽게 기술)

    ### 2. 구조적 분석 및 2차 파급 효과 (Structure & 2nd-order Effects)
    * **데이터 현황 (Data)**: (관련 온체인 데이터, 유동성 집중도, 규제 등 객관적 현황)
    * **예상 파급 효과 (Impact)**: (위 데이터로 인해 발생 가능한 연쇄 효과 및 하방 리스크. '만약 ~라면, ~게 된다' 형태의 논리 전개)

    ### 3. 시장 교차 분석 및 관찰점 (Macro Context & Insight)
    * **거시 환경 연동 (Macro)**: (비트코인 등 거시 지표 또는 전체 자본 흐름과의 상관관계)
    * **핵심 모니터링 지표 (Insight)**: (향후 방향성을 결정지을 정량적 관찰 대상 및 지지/저항 데이터)

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
    print(f"📩 개인 메시지 확인 중 ({bot_username})...")
    check_limit = datetime.now(timezone.utc) - timedelta(hours=4) 
    
    async for msg in client.iter_messages(bot_username, limit=20):
        if msg.date < check_limit: break
        
        if msg.out and msg.text:
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
            
            await bot.send_message(my_channel_id, report_msg)
            
            try:
                await bot.send_message(msg.chat_id, "✅ 분석 완료! 채널을 확인하세요.")
            except:
                pass 
                
            await asyncio.sleep(5)

# 4. 중복 확인
async def get_posted_urls(client, channel_id):
    print("🧹 중복 방지를 위해 최근 게시물 확인 중 (Client)...")
    posted_urls = set()
    try:
        async for msg in client.iter_messages(channel_id, limit=50):
            if msg.text:
                urls = re.findall(r'(https?://\S+)', msg.text)
                if urls:
                    posted_urls.add(urls[0])
    except Exception as e:
        print(f"⚠️ 중복 확인 중 경고: {e}")
        
    return posted_urls

# 5. 메인 실행
async def main():
    print("🧠 심층 분석 봇 가동 (다중 파이프라인 모드)...")
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

    try:
        await process_private_messages(client, bot_username, my_channel_id)
    except Exception as e:
        print(f"⚠️ 개인 메시지 처리 중: {e}")

    posted_urls = await get_posted_urls(client, my_channel_id)
    print(f"🛡️ 이미 처리된 링크 {len(posted_urls)}개 제외 예정")

    chk_time = 14400 # 4시간
    
    for channel in target_channels:
        print(f"📡 {channel} 스캔 중...")
        try:
            async for msg in client.iter_messages(channel, limit=15):
                if (datetime.now(timezone.utc) - msg.date).total_seconds() > chk_time: continue
                
                text = msg.message if msg.message else ""
                urls = re.findall(r'(https?://\S+)', text)
                
                if urls:
                    target_url = urls[0]
                    
                    if target_url in posted_urls:
                        print(f"⏩ 스킵 (이미 분석함): {target_url}")
                        continue
                    
                    content = fetch_content(target_url)
                    if not content: content = text
                    
                    await asyncio.sleep(5) 
                    summary = ai_analyze(content)
                    
                    final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({target_url})\n출처: {channel}"
                    await bot.send_message(my_channel_id, final_msg, link_preview=False)
                    
                    posted_urls.add(target_url)

        except Exception as e:
            print(f"⚠️ {channel} 에러: {e}")
            continue

with client:
    client.loop.run_until_complete(main())
