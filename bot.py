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

# [기능 1] 텍스트만 보낼 때
def send_text_via_bot(chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload)
        return True
    except Exception as e:
        print(f"⚠️ 텍스트 전송 실패: {e}")
        return False

# [기능 2] 사진+텍스트 보낼 때 (NEW!)
def send_photo_via_bot(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            payload = {"chat_id": chat_id, "caption": caption}
            files = {"photo": photo}
            requests.post(url, data=payload, files=files)
        return True
    except Exception as e:
        print(f"⚠️ 사진 전송 실패: {e}")
        return False

async def main():
    await client.start()
    
    # 1. 내 채널 진짜 ID 찾기
    try:
        entity = await client.get_entity(target_channel_username)
        real_bot_id = int(f"-100{entity.id}")
        print(f"✅ 타겟 채널 ID: {real_bot_id}")
    except Exception as e:
        print(f"❌ 채널 찾기 실패: {e}")
        return

    print("뉴스 스캔 시작...")

    # 2. 중복 방지용 최근 글 로딩
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel_username, limit=30):
        # 캡션(사진설명)이 있으면 캡션을, 없으면 텍스트를 저장
        text = msg.message
        if text: recent_my_msgs.append(text)

    # 3. 뉴스 가져오기
    for channel in source_channels:
        try:
            async for msg in client.iter_messages(channel, limit=5):
                # 20분 컷
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 1200: continue

                new_text = msg.message if msg.message else ""
                
                # 중복 검사
                is_duplicate = False
                for old_text in recent_my_msgs:
                    if old_text and is_similar(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    print(f"PASS: 중복 ({channel})")
                    continue

                # [전송 시작]
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    # 메시지 꾸미기
                    final_msg = f"[{source_name}]\n{new_text}"
                    
                    # A. 사진이 있는 경우
                    if msg.photo:
                        print(f"📸 사진 발견! 다운로드 중... ({source_name})")
                        # 사진을 잠시 다운로드
                        path = await client.download_media(msg.photo, file="temp.jpg")
                        # 봇으로 전송
                        send_photo_via_bot(real_bot_id, path, final_msg)
                        # 임시 파일 삭제
                        os.remove(path)
                        print(f"SENT: {source_name} (사진)")

                    # B. 글자만 있는 경우
                    else:
                        send_text_via_bot(real_bot_id, final_msg)
                        print(f"SENT: {source_name} (텍스트)")

                    # 중복 리스트에 추가
                    if new_text: recent_my_msgs.append(new_text)
                    
                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
