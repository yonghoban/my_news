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
    '@eastsouthwind'
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

    # 2. 최근 글 로딩 (중복 방지)
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel_username, limit=30):
        text = msg.message
        if text: 
            clean_text = text.split('\n\n', 1)[-1] if '\n\n' in text else text
            recent_my_msgs.append(clean_text)

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

                # [전송]
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    # === [핵심 수정] 하이퍼링크 생성 ===
                    # 채널 이름에 원본 메시지 링크를 심습니다.
                    # 예: https://t.me/WeCryptoTogether/1234
                    username = channel.replace('@', '') # @ 제거
                    post_link = f"https://t.me/{username}/{msg.id}"
                    
                    # 마크다운 링크 문법: [보여질글자](주소)
                    header = f"**[⏩ {source_name}]({post_link})**\n\n"
                    final_caption = header + new_text
                    # ================================
                    
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
                            link_preview=True # 링크 미리보기 켜기
                        )
                        print(f"SENT: {source_name} (텍스트)")

                    if new_text: recent_my_msgs.append(new_text)
                    
                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
