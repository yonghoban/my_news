import asyncio
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel

# 본인의 API 정보 입력
api_id = 30196101 
api_hash = 'bb48c37a0304c31583d12283c80ff1ed'

# 기존 bot.py에 있던 source_channels 리스트 전체 복사 붙여넣기
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

async def main():
    # 로컬에 세션 파일을 생성하여 안전하게 1회 조회
    client = TelegramClient('local_extractor', api_id, api_hash)
    await client.start()
    
    print("\n\n=== [아래 코드를 복사하여 bot.py에 붙여넣으세요] ===")
    print("from telethon.tl.types import InputPeerChannel\n")
    print("source_channels = [")
    
    for username in source_channels:
        try:
            entity = await client.get_entity(username)
            # 고유 ID와 접근 해시를 InputPeerChannel 객체로 출력
            print(f"    InputPeerChannel({entity.id}, {entity.access_hash}), # {username}")
            await asyncio.sleep(1.5) # Flood Wait 방지용 지연
        except Exception as e:
            print(f"    # 추출 실패 (수동 확인 필요): {username} - {e}")
            
    print("]")
    print("==================================================\n")

asyncio.run(main())
