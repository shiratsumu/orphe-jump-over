# ORPHE JUMP OVER

ORPHE CORE（足に着けるセンサー）で跳んだ高さを推定し、身近なもの（カラーコーン・ドラム缶など）と比べて
「〇〇を飛び越えた！」と最高点の写真に合成して記録するサイト。

- JUMP CAMERA（カメラで記録）: https://shiratsumu.github.io/orphe-jump-over/camera.html
- JUMP ANALYZER（生データ CSV の解析・教師データとの比較）: https://shiratsumu.github.io/orphe-jump-over/


## 公開（GitHub Pages）
サイトは `docs/` だけで動く（ORPHE-CORE.js・テーマ・ロゴは jsDelivr から、手元で確認したコミットに固定して読み込む）。
リポジトリの Settings → Pages → Source を「Deploy from a branch」、ブランチ `main` / フォルダ `/docs` にする。
https で配信されるので、Android の Chrome からもそのままカメラとセンサーが使える。
ORPHE-CORE.js は ORPHE の利用方針（非商用は無償、商用は要契約）に従う。

## 起動（ローカル）
```
cd <このリポジトリのフォルダ>
python3 -m http.server 8000
```
Chrome で http://localhost:8000/docs/ を開き「ORPHE CORE を接続」。
（Web Bluetooth は localhost か https でのみ動作）

生データ CSV をページにドラッグ＆ドロップすると全ジャンプを解析して履歴に表示。
教師データ CSV（manual-gt-…）もドロップすると、動画時刻とセンサー時刻のずれを自動推定して対応付け、
ジャンプごとの差と MAE / RMSE / 偏り / 最大差を表示する。

## ジャンプ記録カメラ（docs/camera.html）
カメラ開始 → センサー接続 → ジャンプ。最高点の写真に「〇〇（約 X cm）を飛び越えた！」と
実寸比のイラストを並べた記録画像を作る（◀▶ でコマ調整、画像保存）。
ライブ映像上の緑の線（地面）・オレンジの線（基準の高さ）・イラスト（跳ぶ位置）をドラッグして合わせておくと、
最高点の写真の地面にイラストを実寸で合成し、足の最高点の線を引く（設定はブラウザに保存）。
「自動で基準を設定」: 身長入力（初回のみ）→ 無人の背景を 3 秒後に記録 → 人が入って 1.5 秒静止したら、
背景差分で切り出した人の頭頂 = 基準（身長）、足裏 = 地面、中心 = イラスト位置に自動で合わせる。
首で途切れた頭（髪など）は体の真上の塊として結合し、それでも上端が肩幅のままなら
肩の高さ ≒ 身長 × 0.82 として頭頂を推定する。
録画を停止すると orphe_session_*.zip に 生データ / 動画 / ジャンプ一覧 / 記録画像 /
calibration.csv（校正ごとの値・検出方法・肩幅など）/ calibration_{background,frame,mask}.png をまとめて保存。
映像右上のアイコンで全画面（右側に記録画像、クリックで拡大表示）。
「録画」で生データ CSV（学習データと同じ形式）・動画・ジャンプ一覧 CSV（動画内の最高点時刻つき）を保存。
スマホ: Mac + iPhone は連係カメラ、Android は公開ページをそのまま開く（ローカルなら `python3 scripts/serve_https.py`）。

## 推定方法（docs/jump.js, analysis/jump_model.py）
1. 踏み切り: |加速度| > 6 G
2. 着地: 踏み切りから 0.25 s 以降で |加速度| > 10 G（空中でも足の振りで ~6 G 出るため別しきい値）
3. クォータニオンで加速度をワールド座標へ → 踏み切り 1.5〜0.5 s 前の静止区間の重力方向に射影 → 2 回積分（離地・着地の高さ 0 で拘束）→ 足の最高点
4. 教師データ（動画の靴底最高点）で線形補正 `cm = 0.8628 * raw + 5.0192`

精度（9 本）: 補正前 MAE 3.96 cm / 1 本抜き交差検証 MAE 2.52 cm / r = 0.992

## 再学習
新しい生データと教師 CSV を用意して
```
python3 analysis/jump_model.py <raw.csv> <manual-gt.csv>   # 補正係数 fit (all) を出力
node analysis/replay_test.js <raw.csv> <manual-gt.csv>     # JS 実装での検証
```
出力された係数を docs/jump.js の `CAL_A`, `CAL_B` に反映する。
