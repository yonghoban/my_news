import os
import asyncio
import requests # 봇 배달을 위해 추가
from telethon import TelegramClient
from telethon.sessions import StringSession
from difflib import SequenceMatcher
from datetime import datetime, timezone

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]
bot_token = os.environ["BOT_TOKEN"] # 새로 추가된 배달부 토큰

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

# 내 채널 (타겟)
target_channel = '@turtleking10' 
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)

def is_similar(text1, text2, threshold=0.90):
    if not text1 or not text2: return False
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

# [NEW] 배달부(Bot)가 메시지를 쏘는 함수
def send_via_bot(text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_channel,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Bot send error: {e}")

async def main():
    await client.start()
    print("봇이 깨어났습니다. 뉴스 확인 중...")

    # 1. 내 채널의 최근 글들을 미리 가져옴 (중복 비교용)
    recent_my_msgs = []
    # 주의: 봇이 보낸 글도 읽어와야 하므로, 여기서는 그냥 최근 글 텍스트만 수집
    async for msg in client.iter_messages(target_channel, limit=30):
        if msg.text: recent_my_msgs.append(msg.text)

    # 2. 감시 대상 채널 순회
    for channel in source_channels:
        try:
            async for msg in client.iter_messages(channel, limit=5):
                # 20분 이상 된 글 무시
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 1200: 
                    continue

                new_text = msg.text if msg.text else ""
                
                # 중복 검사
                is_duplicate = False
                for old_text in recent_my_msgs:
                    if old_text and is_similar(new_text, old_text): # old_text가 None이 아닐때만
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    print(f"PASS: 중복 ({channel})")
                    continue

                # [전송] 봇을 통해 배달! (Unread 배지를 위해)
                # 포워딩 대신 '복사+붙여넣기' 방식을 씁니다.
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    # 메시지 꾸미기
                    final_msg = f"**[{source_name}]**\n{new_text}"
                    
                    # 배달부에게 전송 지시
                    send_via_bot(final_msg)
                    
                    print(f"SENT: {source_name} -> 내 채널 (by Bot)")
                    
                    # 방금 보낸 것도 중복 리스트에 추가
                    if new_text: recent_my_msgs.append(new_text)

                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
