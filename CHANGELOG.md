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
