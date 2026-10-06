# Model conversion

從官方 PyTorch 權重轉出 `models/` 下的 tf.js graph model.

    PyTorch (.pth) -> TensorFlow SavedModel -> tf.js graph model ( float16 )

 - `archs.py`：PyTorch 參考網路, 取自官方原始碼並只保留不切塊的推論路徑, 層名與官方權重一致.
 - `tf_archs.py`：同一個網路的 TensorFlow ( NHWC ) 實作, 直接吃 PyTorch 的 state dict.
 - `convert.py`：載權重 → 建 TF 網路 → 用隨機輸入比對 TF 與 PyTorch 的輸出 ( 誤差超過 1e-3 就中止 ) → 存成 SavedModel → `tensorflowjs_converter --quantize_float16`.
 - `compare.js`：用 `NodeUpscaler` 拿同一張圖跑兩組模型, 輸出像素差統計與結果圖.

沒有走 PyTorch → ONNX → onnx2tf: onnx2tf 在 Real-CUGAN 的 SE block 後面會把 NCHW / NHWC 的維度推錯, 導致轉換失敗.


## 環境

    uv venv -p 3.10 venv
    VIRTUAL_ENV=$PWD/venv uv pip install -r requirements.txt

torch 加 tensorflow 下載量約數百 MB. 網路頻寬有限時, 可以先用 `curl --limit-rate` 下載 wheel, 再用 `uv pip install --offline <wheel>` 從本地安裝.


## 權重

放到 `tools/convert/weights/` ( 已 gitignore ), 或用 `--weights` 指定其他目錄.

| 檔案 | 來源 | sha256 |
|---|---|---|
| realesr-general-x4v3.pth | https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth | 8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292 |
| realesr-general-wdn-x4v3.pth | https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth | 1641f8c4464b9f097c9fdda5589273713f67cf59f3d909e0bd688f0cee269dca |
| realesr-animevideov3.pth | https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth | b8a8376811077954d82ca3fcf476f1ac3da3e8a68a4f4d71363008000a18b75d |
| up2x-latest-*.pth, up4x-latest-*.pth | https://github.com/bilibili/ailab/releases/download/Real-CUGAN/updated_weights.zip ( 54MB, 解開 `updated_weights/` ) | 見下 |

    6cfe3b23687915d08ba96010f25198d9cfe8a683aa4131f1acf7eaa58ee1de93  up2x-latest-conservative.pth
    2e783c39da6a6394fbc250fdd069c55eaedc43971c4f2405322f18949ce38573  up2x-latest-denoise1x.pth
    8188b3faef4258cf748c59360cbc8086ebedf4a63eb9d5d6637d45f819d32496  up2x-latest-denoise2x.pth
    0a14739f3f5fcbd74ec3ce2806d13a47916c916b20afe4a39d95f6df4ca6abd8  up2x-latest-denoise3x.pth
    f491f9ecf6964ead9f3a36bf03e83527f32c6a341b683f7378ac6c1e2a5f0d16  up2x-latest-no-denoise.pth
    a8c8185def699b0883662a02df0ef2e6db3b0275170b6cc0d28089b64b273427  up4x-latest-conservative.pth
    42bd8fcdae37c12c5b25ed59625266bfa65780071a8d38192d83756cb85e98dd  up4x-latest-denoise3x.pth
    aaf3ef78a488cce5d3842154925eb70ff8423b8298e2cd189ec66eb7f6f66fae  up4x-latest-no-denoise.pth

`realesrgan/general_plus` ( RealESRGAN_x4plus.pth ) 與 `anime_plus` ( RealESRGAN_x4plus_anime_6B.pth ) 也可以轉換, 但目前未附在 `models/`, 下載網址與大小見 `models/README.md`.

`realesrgan/general_fast` 是 `realesr-general-x4v3` 與 `realesr-general-wdn-x4v3` 各 0.5 的權重內插 ( DNI ), 等同 Real-ESRGAN 推論腳本的預設 `-dn 0.5`, 也與先前使用的 xororz 轉檔版本一致.


## 轉換

    venv/bin/python convert.py --list
    venv/bin/python convert.py realesrgan/general_fast realcugan/2x-conservative ...

預設輸出到 `models/<type>/<name>-64/`, 會覆蓋現有檔案. 可用 `--out` 先輸出到別處比對, `--tile` 改 tile 大小, `--no-fp16` 輸出 float32 權重 ( 檔案大一倍 ).


## 比對

    node tools/convert/compare.js --a models --b /tmp/out --model realcugan/2x-conservative --image sample.png --out /tmp/cmp
