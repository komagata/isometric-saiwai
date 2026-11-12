# 幸区の小さな地図：データと制約

取得日：2026-11-12。公式資料の説明を要約した非公式の地図です。現況や安全な経路を保証する地図ではありません。

## 範囲・座標

川崎市幸区のOSM行政界（緯度35.5261645–35.5620586、経度139.654139–139.704239）を全て含む、500 mに丸めた周辺付き矩形。EPSG:32654（WGS84 / UTM54N）、X=377500–383000、Y=3932000–3936500 m。描画面積5.5 × 4.5 km。行政界はOpenStreetMapに基づくもので、法的な境界確定資料ではありません。

## 建物

出典：[川崎市2022年度PLATEAUデータ](https://www.geospatial.jp/ckan/dataset/plateau-14130-kawasaki-shi-2022)、**CityGML v4**（標準製品仕様書第4.1版）。[使用ZIP](https://assets.cms.plateau.reearth.io/assets/40/25bd0a-f174-4f55-a9bd-0e6868ece0ae/14130_kawasaki-shi_city_2022_citygml_4_op.zip)。版番号v4と測量年度2022は別の意味です。元データには2015年調査等の属性もあり、全棟が2022年時点の形状とは限りません。

[PLATEAU利用規約](https://www.mlit.go.jp/plateau/site-policy/)に従い加工。現行規約は公共データ利用規約第1.0版（PDL1.0）準拠、CC BY 4.0互換利用も許諾。3D都市モデルの権利は川崎市に帰属。これは国土交通省・川崎市が作成した地図ではありません。

各建物で実ポリゴンのある最高LoD（3→2→1）を一つだけ選択。xlink参照だけのSolidには同じLoDのMultiSurfaceを使用します。緯度・経度・標高の軸順を明示して再投影。高さはCityGML頂点の上下差で、measuredHeight属性も別に保存。階数からの架空の高さや屋根の追加は行っていません。絶対標高を保持し、GSI地形に合わせた平坦化はしていません。大部分がLoD1のため平らな屋根です。周辺余白の横浜市・東京都側には、この川崎市データセットの建物がなく、航空写真のみの場所があります。欠けた建物を架空の形状で埋めてはいません。壁・窓は模式表現、屋根色は航空写真の位置周辺から取得。元のPLATEAU写真テクスチャや上流の精密な屋根アトラス補正は未使用です。

## 地形・航空写真

出典：[地理院タイル](https://maps.gsi.go.jp/development/ichiran.html)を加工して作成。

- seamlessphoto、ズーム17、JPEG：写真の色を減色して地表へ投影。
- dem5a、ズーム15、標高TXT：裸地の地形（DTM）。欠損セルをdem（DEM10B）、ズーム14で補完。
- [使用条件](https://maps.gsi.go.jp/help/use.html)、[国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)。出典と加工を明示。

継ぎ目のないモザイクのため、場所ごとの撮影年・測量年を今回のタイル取得記録から確定していません。取得日を撮影年と読み替えないでください。1 m画像と10 m地形メッシュへのリサンプルは、元の5 m／10 m標高の精度を高めるものではありません。加瀬山の地形を含みます。DTMを樹冠や建物上面のDSMとして扱っていません。

## 神奈川県の実測点群

[Kanagawa, 3D Point Cloud Data / AIGID / AWS Open Data](https://registry.opendata.aws/kanagawa_pointcloud/)（2022航空レーザ、CC BY 4.0）。引用：Kanagawa, 3D Point Cloud Data was accessed on 2026-11-12 from the linked registry.

[提供元説明](https://github.com/aigidjp/opendata_kanagawa_pointcloud/blob/main/README.md)。[取得ディレクトリ](https://kanagawa-pointcloud.s3.ap-northeast-1.amazonaws.com/2022/01/LP/Original/LAS/09/LD/66/)内の09LD6611,6612,6613,6614,6621,6623,6631,6632,6633,6634,6641,6643,6644.zip。各URL・SHA256・取得時刻はsource-manifest.jsonに記録。

LAS format 1をストリーム読み込み。平面直角座標IX系EPSG:6677からUTM54Nへ変換。Tokyo Bay平均海面基準の標高を保持。2 mセルの有効リターン最大値を**実測DSM**として保存、欠損はNaNのままで外挿しません。分類7/18のノイズ点を除外。分類3/4/5の植生点上面も監査用に保持しますが、実データでは加瀬山の高木の多くがこの分類に含まれていません。樹冠候補は実測DSMからGSI DTMを引き、航空写真の緑またはOSM森林を補助マスクとして抽出します。PLATEAU実面を投影した建物フットプリントと外側2 mを除外し、工場屋根を樹木と誤認することを避けています。推定木にも同じ建物除外を適用。屋上庭園や建物に接した樹冠は控えめに省略されます。点群由来地面（分類2/8）も監査用に保持しますが、地形はGSI DTMで統一。ジオイド・標高改定・計測時期の差の補正は未実施です。

**全面点群ではありません**。描画矩形の約30.08%の2 mセルに実測DSMがあります。lidar-coverage.pngは白=点あり・黒=未計測／欠損（北が上）。細かな欠損、樹木の重なり、分類誤りは残ります。樹種は不明、樹冠半径は高さから推定。範囲外はOSMの木、またはOSM公園・森林内の航空写真の緑から配置し、高さを推定8 mと明示。推定木と実測樹冠はtrees.jsonのprovenanceで区別できます。

## OpenStreetMap

© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright)、ODbL 1.0。[Overpass API](https://overpass-api.de/api/interpreter)のキャッシュ済み限定範囲クエリ。道路・線路・水面・土地利用・樹木・POI・行政界を使用。道路方向とoneway=-1、通行制限を反映、車は左側。幅のない道路はクラス別の描画用推定幅です。OSM多重ポリゴンの外周・内周を処理し、穴を塗りつぶしません。

橋の実クリアランスを取得していないため、地表テクスチャ上の表示に留めています。高架道路・トンネルのアニメーション車は省略。全道路の接続性や橋の上下関係を再現していません。アニメーションは装飾で、実交通や渋滞の情報ではありません。夜のランプ位置はOSMで明示された街灯のみですが、発光は模式表現です。

派生地理データと元のOSM取得JSONを**geodata.zip**から取得可能。OSM由来データにはODbLを適用、独立に作成されたPLATEAU・GSI・点群由来のデータには各出典の条件を維持します。source-manifest.jsonに完全な取得記録、集計、制約を含めています。

## 地域カード

独自の短い要約です。写真や長文転載はしません。座標は取得OSMの地点／形状中心に基づき、川・信号場は表示用の文脈地点を明示選択。ユーザーだけが知る話は未提供のため追加していません。

- [川崎市教育委員会：夢見ヶ崎](https://www.city.kawasaki.jp/880/page/0000000051.html)
- [幸区の年表](https://www.city.kawasaki.jp/saiwai/category/109-4-4-0-0-0-0-0-0-0.html)
- [幸区：新鶴見操車場](https://www.city.kawasaki.jp/saiwai/page/0000024752.html)
- [川崎市：地名調査報告書「鹿島田と新川崎」](https://www.city.kawasaki.jp/250/cmsfiles/contents/0000005/5013/r1_chimeihoukoku.pdf)
- [ミューザ川崎シンフォニーホールの歴史](https://kawasaki-sym-hall.jp/about/history/)
- [国土交通省関東地方整備局：多摩川大橋施設情報（表示地点35.55729,139.69654）](https://www.ktr.mlit.go.jp/ktr_content/content/000923702.pdf)
- [ラゾーナ川崎プラザ公式サイト](https://mitsui-shopping-park.com/lazona-kawasaki/)

## 原作・ソフトウェア・音楽

原作：[jankeesvw/isometric-helenaveen](https://github.com/jankeesvw/isometric-helenaveen)、基点8cb8b47。レンダラーとDeep Zoomビューアを改変して使用しています。**チェックアウト内に正式なLICENSEファイルはありません**。READMEは他地域への改変を案内していますが、正式なソフトウェア再配布ライセンスを本作が付与・推定するものではありません。原作者のクレジットを保持し、ライブラリや地理データの利用条件と区別して記載しています。

three.js、Playwright、OpenSeadragon等の権利は各作者に帰属。OpenSeadragon 4.1.1はBSD 3-Clauseで同梱（vendor/OpenSeadragon-LICENSE.txt）。音楽：[My Street](https://opengameart.org/content/my-street)、congusbongus、CC0。ユーザーが音楽をオンにした場合のみ再生。ブラウザのlocalStorageには音楽／夜景設定を記録。GPSカーソルは地図内の計算値で、端末の位置情報は要求しません。
