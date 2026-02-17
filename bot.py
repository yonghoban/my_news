import os
import asyncio
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
    '@eastsouthwind', '@hyperliquid_announcements', '@catallactic', '@narockisrock1', '@househoneybee',
    '@Web3LearningWithInger', '@Dove262', '@mujammin123', '@jh_6598', '@jueokman', '@c0wfarm', 
]

# 내 채널 (사람용 주소)
target_channel_username = '@turtleking10'
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('bot_session', api_id, api_hash)

def is_similar(text1, text2, threshold=0.90):
    if not text1 or not text2: return False
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

async def main():
    print("🚀 봇 시스템 가동 중...")
    await client.start()
    await bot.start(bot_token=bot_token)

    # 1. 타겟 채널 ID 확인
    try:
        entity = await client.get_entity(target_channel_username)
        real_bot_id = int(f"-100{entity.id}")
        print(f"✅ 타겟 채널 ID: {real_bot_id}")
    except Exception as e:
        print(f"❌ 채널 찾기 실패: {e}")
        return

    # 2. 최근 글 로딩 (중복 방지용: 50개까지 비교)
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel_username, limit=50):
        text = msg.message
        if text: 
            # "Forwarded from:" 뒷부분(본문)만 잘라서 저장
            clean_text = text.split('\n\n', 1)[-1] if '\n\n' in text else text
            recent_my_msgs.append(clean_text)

    # 3. 뉴스 가져오기
    for channel in source_channels:
        try:
            # === [핵심 수정 1] 탐색 범위를 5개 -> 30개로 대폭 증가 ===
            async for msg in client.iter_messages(channel, limit=30):
                
                # === [핵심 수정 2] 시간 제한을 20분 -> 6시간(21600초)으로 완화 ===
                # 깃허브가 늦게 돌거나 밀려도 다 가져옵니다. 중복은 위에서 거르니까 안심하세요.
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 21600: 
                    continue

                new_text = msg.message if msg.message else ""
                
                # 중복 검사 (이미 내 채널에 있는 내용은 패스)
                is_duplicate = False
                for old_text in recent_my_msgs:
                    if old_text and is_similar(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue # 중복이면 조용히 넘어감 (로그 생략해서 속도 향상)

                # [전송]
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    # 1. 링크 만들기
                    username = channel.replace('@', '') 
                    post_link = f"https://t.me/{username}/{msg.id}"
                    
                    # 2. 헤더 만들기
                    header = f"↪️ Forwarded from: **[{source_name}]({post_link})**\n\n"
                    final_caption = header + new_text
                    
                    if msg.media:
                        file_path = await client.download_media(msg.media)
                        await bot.send_message(
                            real_bot_id,
                            final_caption,
                            file=file_path,
                            link_preview=False 
                        )
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        print(f"SENT: {source_name} (미디어)")
                    else:
                        await bot.send_message(
                            real_bot_id, 
                            final_caption,
                            link_preview=True 
                        )
                        print(f"SENT: {source_name} (텍스트)")

                    # 방금 보낸 것도 중복 리스트에 즉시 추가 (같은 실행 주기 내 중복 방지)
                    if new_text: recent_my_msgs.append(new_text)
                    
                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
