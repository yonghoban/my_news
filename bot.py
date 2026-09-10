from telethon.tl.types import InputPeerChannel
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
    InputPeerChannel(1396820120, -8277137941562883013), # @WeCryptoTogether
    InputPeerChannel(1465631343, 4774107298271741836), # @lnsanecoin
    InputPeerChannel(1313067241, 4179849229309486201), # @seaotterbtc
    InputPeerChannel(1326359244, 2387840600152227676), # @cryptomouseview
    InputPeerChannel(2179206614, -8382815681236004363), # @jammin0720
    InputPeerChannel(1544137863, 4893880217681789838), # @yobeullyANN
    InputPeerChannel(2373735487, 1383391892532742766), # @justdegenguy
    InputPeerChannel(1733283934, 8996804192263813122), # @moneygrid
    InputPeerChannel(1451407215, -2155480647585030688), # @tlsrltnf
    InputPeerChannel(1510700616, 126884145332118078), # @doriworld
    InputPeerChannel(1259934336, 4181747256265576999), # @Raoni1
    InputPeerChannel(2078740044, -7505065249724735067), # @airdropcosm
    InputPeerChannel(3931856019, -4476899008680814159), # @Gorae_gorae
    InputPeerChannel(2132063118, -1270535778772125772), # @dontworrymomcoinverygood
    InputPeerChannel(2423228517, -3618221212000543395), # @Edenitywl
    InputPeerChannel(3870259445, -3587965899864610750), # @crypto_offroad
    InputPeerChannel(2192941716, 1790244434396455053), # @dolchanchain
    InputPeerChannel(1588820796, -1635300001276390474), # @web3subin
    InputPeerChannel(1856015924, 2489600532520609478), # @ai_masters_community
    InputPeerChannel(2556510058, -6734094317361577873), # @Thoughts_BFox
    InputPeerChannel(1535698497, -2041550562059701111), # @Honeyofwhitesocks_2
    InputPeerChannel(1621568519, 4891274937207605718), # @minchoisfuture
    InputPeerChannel(1864238560, 4029679992058141425), # @doratman18
    InputPeerChannel(1226189796, -4619760585456243986), # @chunjonghyun
    InputPeerChannel(1645555058, 6916182789246563011), # @forevernft
    InputPeerChannel(1806285150, -8543975683639426975), # @KOREAalphaDEGEN
    InputPeerChannel(3020050059, -7088098084828714926), # @saltalpha
    InputPeerChannel(1707333905, -888572553200744054), # @eastgoonercrypto
    InputPeerChannel(1797237914, 931955497981526530), # @juhyukb
    InputPeerChannel(1847658483, -4215261014339353488), # @billair1
    InputPeerChannel(1634677564, 1025528071149100502), # @davidanecdotekr
    InputPeerChannel(1738204270, 3030647438863089676), # @c_ryptodiary
    InputPeerChannel(1588597281, -4835295564971416188), # @dolbikong
    InputPeerChannel(3172464972, 3655865147126395040), # @effort_never_betrays_U
    InputPeerChannel(1652098893, -7348086446374723573), # @magonia_b
    InputPeerChannel(2107531589, -6326581881514395232), # @inhu0
    InputPeerChannel(1908194425, 1738373570129500448), # @cybertruck666
    InputPeerChannel(1319564729, -5007511276717502994), # @moneybottle
    InputPeerChannel(1532523189, 6437918650519547441), # @ResearchSena
    InputPeerChannel(1731411148, 3283842490316362592), # @SasukeChart
    InputPeerChannel(1538528686, 5364019371555046958), # @anancoin
    InputPeerChannel(2574511154, 6896778521666315069), # @easynoscamai
    InputPeerChannel(1761254803, -3726356088876330106), # @BQTelegram
    InputPeerChannel(2342070015, -2366230513395724121), # @chrisdoublepersona
    InputPeerChannel(2237628177, 4733409816282594456), # @gorochi22
    InputPeerChannel(2339532413, -4617350462283659664), # @Hyperliquid_KR_announce
    InputPeerChannel(4405317448, -5847281379384302714), # @Tether_Smugglers
    InputPeerChannel(2408900977, -4033770340707242685), # @Roh0517
    InputPeerChannel(2448633395, -8132615683301792241), # @Plan_G_Research
    InputPeerChannel(1554974037, 1178706745559314501), # @honeymouse1003
    InputPeerChannel(1301520513, 765218452639259980), # @pgyinfo
    InputPeerChannel(1584183723, -5022469109965414623), # @minebuu_cryptoball
    InputPeerChannel(1769342188, 5306367747164752002), # @crypt0_sea
    InputPeerChannel(1230780667, -1925635561861981993), # @gensencoin
    InputPeerChannel(1869932358, 213424257171520199), # @pachepunch
    InputPeerChannel(1808910034, -2658466703422009858), # @BMTube
    InputPeerChannel(1645632215, -4098308677741249983), # @justicekingsman
    InputPeerChannel(2307869453, 4272885985472298163), # @ryotmadness
    InputPeerChannel(2086739233, 2650964270685890237), # @bangguseokcrypto
    InputPeerChannel(1917610401, 3058417795274955803), # @LEEHEESANGDYOR
    InputPeerChannel(1829994590, -7116187817974267719), # @murphybus
    InputPeerChannel(2402400717, 306967358827511164), # @pannpunch
    InputPeerChannel(2214669041, 1995486205604435117), # @therealdyor
    InputPeerChannel(1736699211, 1464071284250190986), # @killberosDAO
    InputPeerChannel(1470829795, 3340137868037219913), # @GODOGtrader
    InputPeerChannel(2279232195, -8362658662893311932), # @SOLful_hodl_life
    InputPeerChannel(2391207730, -1621383852410511176), # @JoshuaDeukKOR
    InputPeerChannel(3654000819, 4789602667142433992), # @metronome812
    InputPeerChannel(1566624832, -4822867803096199397), # @GMBLABS
    InputPeerChannel(3855640363, 3827724325622324551), # @look4treasure
    InputPeerChannel(1577805179, 8519111466183059517), # @channel_dms
    InputPeerChannel(1590774317, 3767957104105471613), # @churin0329
    InputPeerChannel(3904375404, 4686351268041801165), # @all_degens_are_dead
    InputPeerChannel(1631164900, -4029653689883176530), # @SUS_secretnote
    InputPeerChannel(2133256660, 5493068448700184590), # @kastardgood
    InputPeerChannel(2692233584, -7324138082629879353), # @RWAkr
    InputPeerChannel(2508135923, -6303727476614073625), # @cryptoponyo
    InputPeerChannel(1473726267, -7486680835991729310), # @funkyonchain
    InputPeerChannel(2389856356, -5982069441550543731), # @amgnresearch
    InputPeerChannel(2042687149, 5524513589864460688), # @ewlreads
    InputPeerChannel(1447581120, 7983717750465401744), # @gachi2job
    InputPeerChannel(1500490454, -3307969127940787386), # @CoinAlphaNo1
    InputPeerChannel(1591164152, 2392060565423008827), # @jutrobedzielepsze
    InputPeerChannel(2234825371, -2721029656400497646), # @DePIN_AI_Korea
    InputPeerChannel(1737854826, -3095399235733245950), # @JeJeCryptoDiary
    InputPeerChannel(2096221383, -2031020452375952780), # @cctgavong
    InputPeerChannel(1549749423, 5797858655893493369), # @informationdao
    InputPeerChannel(1357074781, 3067719840558471302), # @sohwak
    InputPeerChannel(1811805490, 7271289435579944851), # @dopaminemaxi
    InputPeerChannel(2379279982, 8953928295482919359), # @alpha_feeds
    InputPeerChannel(1720130524, 377819656638366410), # @Newwaves_nft
    InputPeerChannel(1224626870, -3321824835224324672), # @CryptoFamily_ilhyun
    InputPeerChannel(2083348480, -6250030765694386385), # @bitethebulletkr
    InputPeerChannel(1528701712, 4870716781673434046), # @jerryview
    InputPeerChannel(2096672667, 5520248756383551478), # @davesalbum
    InputPeerChannel(2923324679, -7971304287916669382), # @prediction_markets_info
    InputPeerChannel(1809307893, 8332215329163054814), # @kdp_dao
    InputPeerChannel(1324843181, 1148302425594619381), # @DeSpread
    InputPeerChannel(1173057128, -687539842484140112), # @icoroots
    InputPeerChannel(1305258308, -2255583068193618950), # @MusGGul
    InputPeerChannel(3388064904, 3959934382874018439), # @taste_suck
    InputPeerChannel(2722179190, -8912060335313481186), # @overcrypto_doom
    InputPeerChannel(2739764803, -2427237964984779825), # @mdewstable
    InputPeerChannel(2720360052, 7321947057363489790), # @xiticle
    InputPeerChannel(1527165172, 2038091338682110960), # @danielsocialclub
    InputPeerChannel(2313792916, -6146192568564892279), # @chanelnameis
    InputPeerChannel(1562144076, -8926405859012811171), # @CODE007_KR
    InputPeerChannel(2888426629, -8361158253640597609), # @whalemove_trade
    InputPeerChannel(1983031968, 2863895062917587131), # @Info_Arbitrage
    InputPeerChannel(1220905316, -3880827759336350794), # @bokjisaideashare
    InputPeerChannel(1983031968, 2863895062917587131), # @Info_Arbitrage
    InputPeerChannel(1746984526, -4352280999315522460), # @subin_gamefi_lab
    InputPeerChannel(4336928861, -3790617861608702102), # @kbc80
    InputPeerChannel(1730476183, -7530929280656639735), # @coin369369
    InputPeerChannel(2113336245, 888899954831891460), # @gmrvillage
    InputPeerChannel(2138876010, 8548110576709438378), # @eastsouthwind
    InputPeerChannel(1736253760, -8745870935985907903), # @hyperliquid_announcements
    InputPeerChannel(1830958061, -8910784000156449105), # @narockisrock1
    InputPeerChannel(1948387284, 156927520860725459), # @Web3LearningWithInger
    InputPeerChannel(2111377812, 1331163272015361658), # @Dove262
    InputPeerChannel(1741175404, 1976404625206709368), # @mujammin123
    InputPeerChannel(2121770704, -498043317101452955), # @jh_6598
    InputPeerChannel(2693190763, 3154358130256837610), # @jueokman
    InputPeerChannel(2185344588, 3633809012623031231), # @c0wfarm
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
