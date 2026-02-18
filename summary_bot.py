import os, asyncio, re, requests, json, time
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone, timedelta # [수정] timedelta 추가

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

# ... (fetch_content 및 ai_analyze 함수는 성공했던 이전 코드와 동일하게 유지) ...

async def process_private_messages(bot, my_channel_id):
    print("📩 지난 1시간 동안의 개인 메시지 확인 중...")
    
    # 현재 시간으로부터 1시간 10분 전까지 확인 (안전범위)
    check_limit = datetime.now(timezone.utc) - timedelta(hours=1, minutes=10)
    
    # 봇에게 온 개인 메시지 목록 가져오기
    async for msg in bot.iter_messages(None):
        if msg.date < check_limit:
            break
            
        # 내가 보낸 텍스트 메시지이고, 봇이 보낸게 아닐 때 (incoming=True)
        if msg.is_private and msg.text and not msg.out:
            print(f"📝 개인 요청 분석 중: {msg.text[:15]}...")
            
            summary = ai_analyze(msg.text)
            
            # 원본 메시지가 너무 길면 앞부분만 잘라서 표시 (가독성용)
            original_preview = msg.text if len(msg.text) < 150 else msg.text[:150] + "..."
            
            # [핵심] 원본과 분석 결과를 매칭하여 채널에 전송
            report_msg = (
                f"📥 **[Personal Request Report]**\n\n"
                f"💬 **원본 메시지:**\n"
                f"> {original_preview}\n\n"  # 텔레그램 인용구 형식
                f"--- AI 분석 결과 ---\n"
                f"{summary}"
            )
            
            # 1. 채널에 전송
            await bot.send_message(my_channel_id, report_msg)
            # 2. 개인 대화창에도 답장으로 전송
            await msg.reply(f"✅ 요청하신 내용 분석이 완료되어 채널에 게시되었습니다.\n\n{summary}")
            
            await asyncio.sleep(5)

async def main():
    print("🧠 심층 분석 봇 가동 (채널 감시 + 개인 메시지 복습)...")
    await client.start()
    await bot.start(bot_token=bot_token)

    try:
        entity = await client.get_entity(my_channel_username)
        my_channel_id = int(f"-100{entity.id}")
    except Exception as e:
        print(f"❌ 채널 찾기 실패: {e}")
        return

    # 1. 개인 메시지 먼저 처리 (복사해둔 텍스트들)
    await process_private_messages(bot, my_channel_id)

    # 2. 채널 감시 로직 실행
    chk_time = 3600 # 1시간 이내
    for channel in target_channels:
        # ... (기존 채널 스캔 및 분석 코드와 동일) ...
        print(f"📡 {channel} 스캔 중...")
        # (생략: 이전 성공했던 채널 스캔 로직)

with client:
    client.loop.run_until_complete(main())
