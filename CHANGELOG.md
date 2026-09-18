## v0.0.4

 - add `upscaleImageData()`: 直接吃 ImageData 回 ImageData, 省掉呼叫端不需要的圖片編解碼
 - blob <-> ImageData 在沒有 `document` 時改走 `createImageBitmap` / `OffscreenCanvas`, 整包可以在 Web Worker 裡跑


## v0.0.3

 - use dist/node.js for main field in package.json


## v0.0.2

 - reorg repo


## v0.0.1

init release
