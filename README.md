# 幸区の小さな地図

川崎市幸区・神奈川県・日本を、公開された実際の地理データから描く立体ピクセル地図。原作は[jankeesvw / Isometric Helenaveen](https://github.com/jankeesvw/isometric-helenaveen)（8cb8b47）です。three.jsによる等角投影、Deep Zoom、検索、地域カード、回転、音楽、夜景を引き継ぎ、日本のデータに置き換えています。

## ビルド

Python 3.11以上、uv、Node.js/npm、libvips、Playwright Chromiumが必要です。Python依存はpyproject.tomlとuv.lockでプロジェクト内に固定し、グローバルpipは使いません。

```bash
uv sync --locked
npm ci --ignore-scripts
npx playwright install chromium
# 自動取得する限定範囲のOSM、GSI、メタデータ。2回目以降はキャッシュを再利用。
uv run python scripts/fetch.py
SCALE=2 ./build.sh
python3 -m http.server 8000 --directory site
```

大容量の原典は一度だけ取得してdata/rawへ配置します。詳しいURL・版・ライセンスは[DATA_SOURCES.md](DATA_SOURCES.md)。

- `data/raw/plateau/kawasaki-2022-v4.zip`：PLATEAU CityGML v4。
- `data/raw/lidar/09LD*.zip`：記載した13点群ZIPと、取得URL・SHA256・日時の`.source.json`。
- `data/raw/gsi/`、`osm_map.json`、`osm_boundary.json`：fetch.pyが限定範囲・最大3並列・2回までの試行で取得。欠損を黙って架空データへ置換しません。

`./build.sh`は取得確認、再投影、地形・点群、建物、樹木、地表、地域カード、交通、出典マニフェスト、4方向の画像と物体マスク、Deep Zoomを生成します。`SCALE`は画素/mで既定2、4は縦横2倍・画素数4倍。レンダーはdisplayless Chromium。デスクトップのGUI確認にはOmaboxを使います。`./site.sh`は既存レンダーからsiteを再構成します（SCALEを合わせる）。データと成果物はgit対象外です。

出力は`site/map.json`、WebP Deep Zoomタイル、JSONオーバーレイ、source-manifest.json、ダウンロード用geodata.zip。Pagesのリポジトリ配下に置ける相対パスです。OpenSeadragon 4.1.1とBSDライセンス表示を同梱し、フォントは端末の代替フォントを使うため、地図の中核表示は外部CDNに依存しません。

## 精度と範囲

EPSG:32654 / UTM54N。幸区のOSM行政界全体を収めた5.5 × 4.5 kmの周辺付き矩形です。全建物はPLATEAUの実ポリゴンと標高で、最高利用可能LoDを一つだけ使用。地形はGSI DTM、加瀬山も起伏を持ちます。神奈川県2022点群で実測DSMと植生を取得できた範囲は約30%。それ以外の木の高さ8 mは推定です。

屋根の大半はLoD1の平屋根。壁・窓・樹冠の形・交通は様式化、橋の高さは未再現。屋根アトラスの精密な写真整合は未実装です。撮影年と取得日は異なります。詳細な制約・出典は常に画面から読めます。地域の体験談はユーザー提供待ちです。

```bash
uv run python -m unittest discover -s tests -v
node tests/geo.mjs
uv run python -m compileall -q scripts
bash -n build.sh site.sh deploy.sh
node --check render/scene.js
node --check render/run.mjs
git diff --check
```

## 公開

deploy.shは明示したPUBLISH_REPOだけを対象とし、上流作者への書き込みと既存gh-pages履歴の置換を拒否します。原作のREADMEは他地域への改変と公開を案内しています。上流チェックアウト内に正式なLICENSEファイルはなく、本リポジトリで独自のライセンスを追加していません。原作者・使用ライブラリ・データのクレジットを維持しています。
