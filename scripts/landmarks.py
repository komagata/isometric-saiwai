"""Concise source-linked local cards. Coordinates from cached OSM geometry or explicit river/rail location.
No resident anecdotes are invented; user-only stories remain pending.
"""
import json
from config import BUILD
from geo import wgs_to_rd
from japan import height
CHRON='https://www.city.kawasaki.jp/saiwai/category/109-4-4-0-0-0-0-0-0-0.html'
CARDS=[
 ('夢見ヶ崎動物公園 / 加瀬山',35.54916456,139.66564829,'公園・古墳','住宅地の中に残る加瀬山の丘。動物公園だけでなく古墳群もあり、川崎市の文化財案内はこの場所の歴史を紹介している。','https://www.city.kawasaki.jp/880/page/0000000051.html'),
 ('新川崎駅',35.5515835,139.6717821,'駅','1980年に横須賀線の駅が開設された。旧新鶴見操車場の周辺では、その後も土地利用の転換が進められてきた。',CHRON),
 ('鹿島田駅',35.5515471,139.6750133,'駅','南武線の鹿島田駅。近くの新川崎駅とは別の路線にあり、二つの駅の間にも市街地が広がっている。','https://www.city.kawasaki.jp/250/cmsfiles/contents/0000005/5013/r1_chimeihoukoku.pdf'),
 ('ミューザ川崎',35.5311897,139.6947779,'音楽','川崎駅西口のコンサートホール。ミューザ川崎シンフォニーホールは2004年7月に開館した。','https://kawasaki-sym-hall.jp/about/history/'),
 ('ラゾーナ川崎プラザ',35.53370181,139.69614998,'商業施設','川崎駅西口にある商業施設。施設の輪郭や周囲の通路は、地図上でも駅前の大きなまとまりとして見える。','https://mitsui-shopping-park.com/lazona-kawasaki/'),
 ('幸区役所',35.5438485,139.6873821,'公共施設','幸区は1972年の川崎市の政令指定都市移行に伴って誕生した。区の年表には、1975年の区役所移転新築も記されている。',CHRON),
 ('多摩川 / 多摩川大橋',35.55729,139.69654,'川・橋','幸区の北東側を流れる多摩川。多摩川大橋は1949年に完成したと、区の年表に記されている。',CHRON),
 ('新鶴見信号場 / 旧操車場',35.5451,139.6733,'鉄道の歴史','1929年に動き始めた新鶴見操車場は、貨物輸送を支えた。1984年に操車場としての役割を終え、信号場などの機能が残った。','https://www.city.kawasaki.jp/saiwai/page/0000024752.html'),
]
def main():
    spots=[]
    for name,lat,lon,kind,text,url in CARDS:
        x,y=wgs_to_rd(lat,lon)
        spots.append(dict(name=name,x=x,y=y,h=float(height(x,y))+3,kind=kind,text=text,more=url,note='公式資料に基づく紹介',coordinate_source='OSM 2026-11-12; river/rail contextual point explicitly selected'))
    (BUILD/'landmarks.json').write_text(json.dumps(dict(places=spots,hotspots=spots,categories=[dict(key='saiwai',label='幸区をめぐる',names=[p['name'] for p in spots])]),ensure_ascii=False,indent=2))
    print(f'{len(spots)} factual local cards')
if __name__=='__main__':main()
