import os
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
from difflib import SequenceMatcher
from datetime import datetime, timezone

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"]

# 감시할 채널들
source_channels = [
    '@WeCryptoTogether', '@lnsanecoin', '@seaotterbtc', '@cryptomouseview', '@jammin0720',
    '@yobeullyANN', '@justdegenguy', '@moneygrid', '@tlsrltnf', '@doriworld', 
    '@Raoni1', '@airdropcosm', '@Gorae_gorae', '@dontworrymomcoinverygood', '@Edenitywl', 
    '@crypto_offroad', '@dolchanchain', '@baroBTC', '@web3subin', '@ai_masters_community', 
    '@Thoughts_BFox', '@Honeyofwhitesocks_2', '@minchoisfuture', '@doratman18', '@Gorae_Insight', 
    '@chunjonghyun', '@forevernft', '@yieldagg', '@KOREAalphaDEGEN', '@saltalpha', 
    '@eastgoonercrypto', '@juhyukb', '@billair1', '@davidanecdotekr', '@vinilbongz', 
    '@c_ryptodiary', '@dolbikong', '@effort_never_betrays_U', '@magonia_b', '@inhu0', 
    '@cybertruck666', '@moneybottle', '@ResearchSena', '@SasukeChart', '@anancoin', 
    '@easynoscamai', '@BQTelegram', '@chrisdoublepersona', '@gorochi22', '@Hyperliquid_KR_announce', 
    '@Tether_Smugglers', '@Roh0517', '@Plan_G_Research', '@honeymouse1003', '@pgyinfo', 
    '@minebuu_cryptoball', '@crypt0_sea', '@gensencoin', '@pachepunch', '@BMTube', 
    '@justicekingsman', '@ryotmadness', '@bangguseokcrypto', '@LEEHEESANGDYOR', '@murphybus', 
    '@pannpunch', '@therealdyor', '@killberosDAO', '@GODOGtrader', '@SOLful_hodl_life', 
    '@JoshuaDeukKOR', '@metronome812', '@GMBLABS', '@look4treasure', '@channel_dms', 
    '@churin0329', '@all_degens_are_dead', '@SUS_secretnote', '@kastardgood', '@RWAkr', 
    '@cryptoponyo', '@funkyonchain', '@amgnresearch', '@ewlreads', '@gachi2job', 
    '@CoinAlphaNo1', '@jutrobedzielepsze', '@DePIN_AI_Korea', '@JeJeCryptoDiary', '@cctgavong', 
    '@informationdao', '@sohwak', '@dopaminemaxi', '@alpha_feeds', '@Newwaves_nft', 
    '@CryptoFamily_ilhyun', '@bitethebulletkr', '@jerryview', '@davesalbum', '@prediction_markets_info', 
    '@kdp_dao', '@DeSpread', '@icoroots', '@MusGGul', '@taste_suck', 
    '@overcrypto_doom', '@mdewstable', '@xiticle', '@danielsocialclub', '@chanelnameis', 
    '@CODE007_KR', '@whalemove_trade', '@Info_Arbitrage', '@bokjisaideashare', '@Info_Arbitrage', 
    '@subin_gamefi_lab', '@gorochidangi', '@kbc80', '@coin369369', '@gmrvillage', 
    '@eastsouthwind'
]

# 내 채널 (사람용 주소)
target_channel_username = '@turtleking10'
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)

def is_similar(text1, text2, threshold=0.90):
    if not text1 or not text2: return False
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

# [NEW] 확실하게 전송하고 결과 확인하는 함수
def send_via_bot(chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id, # 이제 정확한 숫자 ID를 씁니다
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True # 성공!
        else:
            print(f"⚠️ [전송 실패] 원인: {response.text}") # 에러 원인 출력
            return False
    except Exception as e:
        print(f"⚠️ [통신 에러]: {e}")
        return False

async def main():
    await client.start()
    
    # 1. 내 채널의 '진짜 숫자 ID' 알아내기 (Userbot의 능력 사용)
    try:
        entity = await client.get_entity(target_channel_username)
        # 텔레그램 채널 ID 규칙: 앞에 -100을 붙여야 봇이 인식함
        real_bot_id = int(f"-100{entity.id}")
        print(f"✅ 채널 확인 완료! 봇용 ID: {real_bot_id}")
        
        # [테스트] 봇 생존 신고
        if send_via_bot(real_bot_id, "🟢 봇 연결 성공! 뉴스 감시를 시작합니다."):
            print("🔔 테스트 메시지 전송 성공")
        else:
            print("❌ 테스트 메시지 전송 실패 (위 에러 로그 확인)")
            
    except Exception as e:
        print(f"❌ 채널을 찾을 수 없습니다: {e}")
        return

    print("뉴스 스캔 시작...")

    # 2. 최근 글 목록 가져오기
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel_username, limit=30):
        if msg.text: recent_my_msgs.append(msg.text)

    # 3. 뉴스 가져오기
    for channel in source_channels:
        try:
            async for msg in client.iter_messages(channel, limit=5):
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 1200: continue # 20분

                new_text = msg.text if msg.text else ""
                
                # 중복 검사
                is_duplicate = False
                for old_text in recent_my_msgs:
                    if old_text and is_similar(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    print(f"PASS: 중복 ({channel})")
                    continue

                # [전송]
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    final_msg = f"**[{source_name}]**\n{new_text}"
                    
                    # 봇에게 '진짜 ID'로 배달 시킴
                    if send_via_bot(real_bot_id, final_msg):
                        print(f"SENT: {source_name} -> 내 채널 (성공)")
                        if new_text: recent_my_msgs.append(new_text)
                    
                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
