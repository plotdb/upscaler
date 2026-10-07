## v0.0.5

 - `src/index.js` 整個重寫 ( clean-room, 只依規格不看舊碼 ), 切塊 / 合併 / 快取流程不再是 xororz/web-realesrgan ( GPL ) 的衍生程式碼; 連同 0.0.4 自行轉換的模型, 整包已不含 GPL 衍生物
 - 合併改用加權平均: tile 重疊區做線性漸變後除以權重, 取代直接覆蓋, 消掉 tile 接縫
 - 小圖修正: 寬或高小於 tileSize 時先 edge replicate 補到一個 tile, 輸出再裁回原尺寸, 1x1 / 1x300 這類尺寸都能跑
 - alpha 不再被丟掉: 輸入有半透明像素時, alpha 以雙線性放大後放回; 全不透明時輸出 255
 - 新增 `signal` 選項, `upscale()` / `upscaleImageData()` 可用 `AbortController` 中途取消, 取消時不留 tensor
 - 放大倍數改由模型的 input / output shape 推算, `scale` 只用來挑模型檔; 與模型不符時以模型為準
 - 選項驗證: `modelType` / `denoise` / `model` 給錯值在建構時就丟出清楚的錯誤, 不再是載入時 404
 - `warmup()` 共用同一個載入中的 promise, 同時多次呼叫只載入一次; `dispose()` 後可以再 warmup
 - float -> 0~255 改為四捨五入再 clamp; tile 取樣改用 `tf.slice` 與非同步 `data()`, 不再逐像素 JS 迴圈與 `dataSync()`
 - node 擴充點改為文件化的 `decode()` / `encode()` / `loadModel()` hook, 取代原本的私有方法
 - 新增 `margin` 選項 ( 混合前先丟棄 tile 邊緣像素, 預設 0 ) 與 `debug` 選項
 - 依賴整理: 原本的 dependencies 全部移到 devDependencies, 安裝時不再連帶安裝 tfjs-node / canvas / 範例頁套件; `@tensorflow/tfjs`、`@tensorflow/tfjs-node`、`canvas` 改列為 optional peerDependencies, 由使用端自行安裝
 - IndexedDB 快取 key 加上 `plotdb-v1-` 前綴, 確保改用自行轉換的模型; 載入時順便移除舊 key 的快取


## v0.0.4

 - add `upscaleImageData()`: 直接吃 ImageData 回 ImageData, 省掉呼叫端不需要的圖片編解碼
 - blob <-> ImageData 在沒有 `document` 時改走 `createImageBitmap` / `OffscreenCanvas`, 整包可以在 Web Worker 裡跑
 - 模型改為從官方 PyTorch 權重自行轉換 ( `tools/convert/` ), 取代 xororz 的 GPL 轉檔; 涵蓋 realesrgan general_fast / anime_fast 與全部 realcugan 模型, 輸出與舊版一致
 - 移除缺少權重的 realesrgan `general_plus` / `anime_plus` ( 轉換方式見 `models/README.md` ), Real-ESRGAN 預設模型改為 `anime_fast`


## v0.0.3

 - use dist/node.js for main field in package.json


## v0.0.2

 - reorg repo


## v0.0.1

init release
