import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChatForwardsRestrictedError
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone

# === [설정 영역] ===
# 깃허브 비밀금고에서 꺼내 쓰는 정보들
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION"]

# ▼ 감시할 채널들 (여기에 추가하세요)
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

# ▼ 내 채널 (타겟)
target_channel = '@turtleking10' 
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)

def is_similar(text1, text2, threshold=0.90):
    if not text1 or not text2: return False
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

async def main():
    await client.start()
    print("봇이 깨어났습니다. 지난 뉴스를 확인합니다...")

    # 1. 내 채널의 최근 글들을 미리 가져옴 (중복 비교용)
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel, limit=30):
        if msg.text: recent_my_msgs.append(msg.text)

    # 2. 감시 대상 채널 순회
    for channel in source_channels:
        try:
            # 각 채널에서 '최근 15분 이내'에 올라온 글만 가져옴 (limit=3)
            # 깃허브가 15분마다 도니까, 그 사이에 올라온 것만 보면 됨
            async for msg in client.iter_messages(channel, limit=5):
                # 너무 오래된 글(20분 이상)은 무시
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 1200: # 20분
                    continue

                new_text = msg.text if msg.text else ""
                
                # 중복 검사
                is_duplicate = False
                for old_text in recent_my_msgs:
                    if is_similar(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    print(f"PASS: 중복된 내용 ({channel})")
                    continue

                # 전송 (포워딩)
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    await client.forward_messages(target_channel, msg)
                    print(f"SENT: {source_name} -> 내 채널")
                    
                    # 방금 보낸 것도 중복 리스트에 추가 (이번 실행 중에 또 안 보내게)
                    if new_text: recent_my_msgs.append(new_text)

                except ChatForwardsRestrictedError:
                    # 포워딩 금지면 복사해서 보냄
                    await client.send_message(target_channel, f"**[{source_name}]** (🔒포워딩 불가)\n{new_text}")
                except Exception as e:
                    print(f"Error forwarding from {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝. 봇이 다시 잠듭니다.")

with client:
    client.loop.run_until_complete(main())
