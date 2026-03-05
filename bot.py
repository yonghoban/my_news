import os
import asyncio
import re
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime, timezone

# === [설정 영역] ===
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
session_string = os.environ["TELEGRAM_SESSION_1"]
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
    '@crypto_offroad', '@dolchanchain', '@web3subin', '@ai_masters_community', 
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

target_channel_username = '@turtleking10'
# ===================

client = TelegramClient(StringSession(session_string), api_id, api_hash)
bot = TelegramClient('bot_session', api_id, api_hash)

# [중복 방지 1] URL 추출
def extract_urls(text):
    if not text: return set()
    return set(re.findall(r'(https?://[^\s]+)', text))

# [중복 방지 2] 튜닝된 다중 필터 및 부피 우회 로직
def is_duplicate_post(new_text, old_text):
    if not new_text or not old_text: return False
    
    if new_text in old_text or old_text in new_text:
        return True
        
    new_urls = extract_urls(new_text)
    old_urls = extract_urls(old_text)
    if new_urls and old_urls and new_urls.intersection(old_urls):
        return True

    clean_new = re.sub(r'[^\w\s]', '', new_text).split()
    clean_old = re.sub(r'[^\w\s]', '', old_text).split()
    
    set_new = set(clean_new)
    set_old = set(clean_old)
    
    len_new = len(set_new)
    len_old = len(set_old)
    
    if len_new == 0 or len_old == 0: return False
    
    intersection_count = len(set_new.intersection(set_old))
    min_word_count = min(len_new, len_old)
    
    if min_word_count < 10: 
        return False
        
    similarity = intersection_count / min_word_count
    
    if similarity >= 0.65:
        if len_new > (len_old * 1.25):
            print(f"💡 방장 코멘트 추가 감지 우회 (유사도 {similarity:.2f}, 팽창률 {len_new/len_old:.2f}배)")
            return False
        return True

    return False

async def main():
    print("🚀 봇 시스템 가동 중...")
    await client.start()
    await bot.start(bot_token=bot_token)

    try:
        entity = await client.get_entity(target_channel_username)
        real_bot_id = int(f"-100{entity.id}")
        print(f"✅ 타겟 채널 ID: {real_bot_id}")
    except Exception as e:
        print(f"❌ 채널 찾기 실패: {e}")
        return

    # [수정] 기억 용량 1000개로 상향
    recent_my_msgs = []
    async for msg in client.iter_messages(target_channel_username, limit=1000):
        text = msg.message
        if text: 
            if '\n\n' in text:
                clean_text = text.split('\n\n', 1)[-1]
            else:
                clean_text = text
            recent_my_msgs.append(clean_text)

    for channel in source_channels:
        try:
            async for msg in client.iter_messages(channel, limit=30):
                # [수정] 스캔 범위를 2시간(7200초)으로 단축
                time_diff = datetime.now(timezone.utc) - msg.date
                if time_diff.total_seconds() > 7200: continue

                new_text = msg.message if msg.message else ""
                
                is_ad = False
                for keyword in ad_keywords:
                    if keyword in new_text: 
                        is_ad = True
                        break
                if is_ad: continue

                if not new_text.strip():
                    continue

                is_duplicate = False
                for old_text in recent_my_msgs:
                    if is_duplicate_post(new_text, old_text):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue

                try:
                    chat = await client.get_entity(channel)
                    source_name = chat.title
                    
                    username = channel.replace('@', '') 
                    post_link = f"https://t.me/{username}/{msg.id}"
                    
                    header = f"↪️ Forwarded from: **[{source_name}]({post_link})**\n\n"
                    final_caption = header + new_text
                    
                    if msg.media:
                        file_path = await client.download_media(msg.media)
                        
                        if len(final_caption) <= 1000:
                            await bot.send_message(
                                real_bot_id,
                                final_caption,
                                file=file_path,
                                link_preview=False 
                            )
                        else:
                            await bot.send_message(real_bot_id, file=file_path)
                            await bot.send_message(
                                real_bot_id,
                                final_caption,
                                link_preview=False
                            )
                            
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        print(f"SENT: {source_name} (미디어 처리 완료)")
                    else:
                        await bot.send_message(
                            real_bot_id, 
                            final_caption,
                            link_preview=True 
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
