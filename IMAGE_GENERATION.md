# 生成画像の配置

ChatGPT（image_gen）で生成した12カット入りの画像（3列×4行）を、1カットずつのJPEGに切り分けて使っています。

- 元画像（公開しない）: `src/source-images/renew-photo-atlas.png`（1448×1086px）
- 公開用: `src/static/assets/img/photos/00-car-black.jpg` 〜 `11-tools.jpg`（各476×265px、合計約600KB）
- ページ内の指定: `{{photo:0}}` 〜 `{{photo:11}}`（`:eager` を付けると先読み。ヒーロー用）
- 代替テキスト: `src/build.py` の `PHOTOS`

| 番号 | ファイル | 主な使用箇所 |
|---|---|---|
| 0 | 00-car-black | TOPヒーロー |
| 1 | 01-buffing | 代表メッセージ（TOP・CONCEPT）、サブスクのヒーロー |
| 2 | 02-car-silver | フル施工のヒーロー、TOP「県外からのご依頼」 |
| 3 | 03-foam-wash | サブスクのカード、WASH |
| 4 | 04-polisher | フル施工のカード、POLISH、店舗情報 |
| 5 | 05-coating | COATING、部分コーティング |
| 6 | 06-headlight | 個別メニューのカード、ヘッドライト |
| 7 | 07-glass-water | ガラス撥水 |
| 8 | 08-wheel | ホイール |
| 9 | 09-interior | 内装 |
| 10 | 10-booth | TOPサブスク帯、店舗情報 |
| 11 | 11-tools | 店舗情報 |

施工事例（WORKS）は `WORKS` にデータが入るまで、写真タイルと「準備中」の一文だけを表示します。

## 解像度について（要対応）

1カットが約480px幅しかないため、全画面のヒーローやページ見出しの背景では3〜6倍に引き伸ばされ、ぼやけて見えます（特にスマホの縦長ヒーロー）。
次に生成するときは **1カットずつ個別に**、次のサイズで書き出してください。同じファイル名で `photos/` に上書きすれば、そのまま反映されます。

- ヒーロー・ページ見出し（00・01・02・10）: 横2400px以上（16:9）。スマホ用に縦長（9:16）版もあると理想的
- カード・工程写真（その他）: 横1200px以上

代表者本人・実在の店舗・実際の施工事例ではないため、サイト下部に「写真はイメージです（AI生成を含みます）」と表示しています。店舗情報の「工房・設備」には個別に注記を入れています。

## 生成プロンプト

Use case: photorealistic-natural.
Create ONE photographic asset atlas for a premium Japanese car detailing website. EXACT GRID: 3 equal columns by 4 equal rows, 12 edge-to-edge rectangular photographs, no gutters, no borders, no text. Overall aspect ratio 4:3; each individual tile is 16:9. High resolution, ideally 3840x2880. Every boundary exactly on one-third width and one-quarter height. The grid will be cropped programmatically so NEVER overlap images across cells.
Consistent restrained luxury editorial photography: graphite black and silver cars, neutral white strip lighting reflected in glossy paint, realistic textures, dark charcoal studio, no logos, no readable license plates, no watermarks. Each cell has its subject centered, generous room for cropping to portrait. Not a webpage or mockup.
Row 1 left: cinematic close three-quarter front view of a polished black luxury coupe in a dark studio, sweeping white reflections on hood, quiet dark upper background for website hero copy.
Row 1 middle: close hands wearing black nitrile gloves carefully buffing black car body with folded microfiber cloth, no face or identifiable person.
Row 1 right: dramatic glossy silver sports coupe in professional dark detailing bay, full three-quarter side view.
Row 2 left: foam wash, thick white lather on dark car hood, gloved hand using wash mitt.
Row 2 middle: close-up of gloved hands using professional orbital polisher flat against black car hood, correct round foam pad contact.
Row 2 right: close-up of black gloved hand applying ceramic coating with small rectangular applicator to glossy black car body.
Row 3 left: precise macro of modern clean crystal-clear car headlight, dark paint, no branding.
Row 3 middle: macro of round water droplets beading on car windshield, diagonal glass surface.
Row 3 right: close-up immaculate graphite multi-spoke alloy wheel and clean black tire.
Row 4 left: elegant clean black leather car interior, stitching and center console, unbranded.
Row 4 middle: tidy empty generic detailing booth, straight white LED light strips, charcoal walls and clean floor, no signage.
Row 4 right: professional detailing tools neatly arranged on dark workbench, orbital polisher, folded gray microfiber towels, blank unlabeled bottles and foam pads.

