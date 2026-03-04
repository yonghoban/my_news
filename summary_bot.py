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
session_string = os.environ["TELEGRAM_SESSION_2"]
bot_token = os.environ["BOT_TOKEN"]
gemini_api_key = os.environ["GEMINI_API_KEY"]

target_channels = ['@cookiesreads', '@somoreads', '@iansintel', '@icodrops']
my_channel_username = '@turtleking11' 

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('summary_bot_session', api_id, api_hash)

# 1. 링크 내용 추출 파이프라인
def fetch_content(url):
    print(f"🔍 링크 파싱 시도: {url}")
    
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

# 2. Gemini AI 분석 (초간결 모델)
def ai_analyze(text, url_type="article"):
    models = ["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-flash-lite-latest"]
    
    prompt = f"""
    You are a crypto news summarizer for beginners.
    Translate and summarize the following text into Korean.
    
    [Rules]
    1. Output STRICTLY in Korean.
    2. 복잡한 구조나 양식을 모두 버리고, 가장 쉽고 간결한 문장으로 작성할 것.
    3. 전체 내용을 3~4문장 이내로 최대한 압축할 것 (짧은 불렛포인트 사용 권장).
    4. '무엇이 핵심 팩트인가'와 '그것이 투자자에게 어떤 의미인가' 두 가지만 직관적으로 전달할 것.
    5. 어려운 전문 용어는 배제하거나 쉬운 일상어로 대체할 것.

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
        # [수정] 제한을 200개로 상향
        async for msg in client.iter_messages(channel_id, limit=200):
            if msg.text:
                urls = re.findall(r'(https?://\S+)', msg.text)
                if urls:
                    posted_urls.add(urls[0])
    except Exception as e:
        print(f"⚠️ 중복 확인 중 경고: {e}")
        
    return posted_urls

# 5. 메인 실행 (시계열 병합 로직 탑재)
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

    # [수정] 스캔 범위를 2시간(7200초)으로 단축
    chk_time = 7200 
    
    for channel in target_channels:
        print(f"📡 {channel} 스캔 중...")
        try:
            raw_msgs = []
            async for msg in client.iter_messages(channel, limit=15):
                if (datetime.now(timezone.utc) - msg.date).total_seconds() > chk_time: continue
                raw_msgs.append(msg)
            
            if not raw_msgs: continue
            
            raw_msgs.sort(key=lambda x: x.date)
            
            merged_posts = []
            for msg in raw_msgs:
                text = msg.message if msg.message else ""
                
                if merged_posts and (msg.date - merged_posts[-1]['date']).total_seconds() <= 5:
                    merged_posts[-1]['text'] += "\n\n" + text
                else:
                    merged_posts.append({
                        'id': msg.id,
                        'date': msg.date,
                        'text': text
                    })
            
            for post in merged_posts:
                text = post['text']
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
                    
                    username = channel.replace('@', '')
                    post_link = f"https://t.me/{username}/{post['id']}"
                    
                    final_msg = f"🔍 **[Simplex AI Report]**\n\n{summary}\n\n🔗 [원본]({post_link})\n출처: {channel}"
                    await bot.send_message(my_channel_id, final_msg, link_preview=False)
                    
                    posted_urls.add(target_url)

        except Exception as e:
            print(f"⚠️ {channel} 에러: {e}")
            continue

with client:
    client.loop.run_until_complete(main())
