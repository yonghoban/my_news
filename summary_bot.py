import os, asyncio, re, requests, json, time
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone, timedelta

# ... (기존 설정 및 함수 부분 생략) ...

async def process_private_messages(bot, my_channel_id):
    print("📩 개인 메시지(텍스트/URL) 확인 중...")
    
    # 1시간 10분 전까지의 메시지 검사 (GitHub Actions 주기 대응)
    check_limit = datetime.now(timezone.utc) - timedelta(hours=1, minutes=10)
    
    async for msg in bot.iter_messages(None):
        if msg.date < check_limit:
            break
            
        if msg.is_private and msg.text and not msg.out:
            # 1. 메시지 내에 URL이 포함되어 있는지 확인
            urls = re.findall(r'(https?://\S+)', msg.text)
            
            if urls:
                # URL이 있는 경우: 사이트 접속 시도
                target_url = urls[0]
                print(f"🔗 URL 감지 분석 시작: {target_url}")
                content = fetch_content(target_url) # Jina AI 활용
                
                if content:
                    summary = ai_analyze(content, url_type="article")
                    source_label = f"🔗 **원본 링크:** {target_url}"
                else:
                    # 사이트 읽기 실패 시 텍스트만 분석
                    summary = ai_analyze(msg.text, url_type="short_text")
                    source_label = "⚠️ (사이트 접속 실패로 보낸 메시지만 분석함)"
            else:
                # URL이 없는 경우: 텍스트 바로 분석
                print("📝 텍스트 메시지 분석 시작...")
                summary = ai_analyze(msg.text, url_type="short_text")
                source_label = "📝 직접 입력한 텍스트"

            # 2. 결과 리포트 구성 (원본 메시지 포함)
            original_preview = msg.text if len(msg.text) < 100 else msg.text[:100] + "..."
            report_msg = (
                f"📥 **[Personal Request Report]**\n\n"
                f"💬 **원본 내용:**\n"
                f"> {original_preview}\n\n"
                f"{source_label}\n"
                f"--- AI 분석 결과 ---\n"
                f"{summary}"
            )
            
            await bot.send_message(my_channel_id, report_msg)
            await msg.reply(f"✅ 분석 완료! 채널에 게시되었습니다.")
            
            await asyncio.sleep(5) # API 보호

# ... (이하 main 로직 동일) ...
