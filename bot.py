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

# [광고 금지어 목록]
ad_keywords = [
    "#ad", "#광고", "유료광고", "소정의 고료", "가입링크", 
    "거래소 가입", "증정금", "협찬", "파트너십", 
    "Sponsored", "Promo", "referral", "register", "sign up",
    "입금 이벤트", "가입 이벤트"
]

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
    '@eastsouthwind',
    '@hyperliquid_announcements', '@narockisrock1', '@Web3LearningWithInger', 
    '@Dove262', '@mujammin123', '@jh_6598', '@jueokman', '@c0wfarm'
]

# 내 채널 (사람용 주소)
target_channel_username = '@turtleking10'
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('bot_session', api_id, api_hash)

# [중복 방지] 텍스트 정규화 (공백 제거 후 비교)
def normalize_text(text):
    if not text: return ""
    return "".join(text.split())

def is_similar(text1, text2, threshold=0.90):
    if not text1 or not text2: return False
    # 정규화된 텍스트로 비교 (더 정확함)
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    return SequenceMatcher(None, norm1, norm2).ratio() >= threshold

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

    # 2. 최근 글 로딩 (기억력 4배 강화: 200개)
    recent_my_msgs = []
    # limit=200 으로 늘려서 놓치는 중복이 없도록 함
    async for msg in client.iter_messages(target_channel_username, limit=200):
        text = msg.message
        if text: 
            # 헤더(Forwarded from...) 제거하고 본문만 추출
            if '\n\n' in text:
                # 첫 번째 줄바꿈 이후가 본문일 확률이 높음
                clean_text = text.split('\n\n', 1)[-1]
            else:
                clean_text = text
            recent_my_msgs.append(clean_text)

    # 3. 뉴스 가져오기
    for channel in source_channels:
        try:
            async for msg in client.iter_messages(channel, limit=30):
                # 6시간 이내
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 21600: continue

                new_text = msg.message if msg.message else ""
                
                # [광고 필터링]
                is_ad = False
                for keyword in ad_keywords:
                    if keyword in new_text: 
                        is_ad = True
                        break
                if is_ad: continue

                # [중복 검사]
                # 텍스트가 아예 없으면(사진만 있으면) 중복 체크가 어려워 패스할 수도 있으나,
                # 일단 텍스트가 있는 경우만 철저히 검사
                if not new_text.strip():
                    continue # 캡션 없는 이미지는 중복 위험이 커서 일단 건너뜀 (안전빵)

                is_duplicate = False
                for old_text in recent_my_msgs:
                    # 1. 완전히 똑같은 경우 (빠른 처리)
                    if new_text in old_text: 
                        is_duplicate = True
                        break
                    # 2. 90% 이상 비슷한 경우 (미세한 차이)
                    if is_similar(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue

                # [전송]
                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    username = channel.replace('@', '') 
                    post_link = f"https://t.me/{username}/{msg.id}"
                    
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

                    # 방금 보낸 것도 즉시 기억 목록에 추가
                    if new_text: recent_my_msgs.append(new_text)
                    
                except Exception as e:
                    print(f"Error processing {channel}: {e}")

        except Exception as e:
            print(f"Error checking {channel}: {e}")

    print("확인 끝.")

with client:
    client.loop.run_until_complete(main())
