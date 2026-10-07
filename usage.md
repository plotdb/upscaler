# Web Upscaler 使用範例


## 可用模型一覽

支援兩種模型類型：

 - `realcugan`：Real-CUGAN，支援 2x / 4x 放大，快速，適合動漫，模型小（約 3MB）
 - `realesrgan`：Real-ESRGAN，支援 4x 放大，適合照片與動漫，目前附的 fast 版模型約 1-3MB

Real-CUGAN `denoise` 選項：

 - `conservative`：保守降噪（推薦），支援 2x / 4x
 - `no-denoise`：不降噪，支援 2x / 4x
 - `denoise1x`：輕度降噪，僅 2x
 - `denoise2x`：中度降噪，僅 2x
 - `denoise3x`：強力降噪，支援 2x / 4x

Real-ESRGAN `model` 選項：

 - `anime_fast`：動漫快速版
 - `anime_plus`：動漫高品質版（目前未附，見 `models/README.md`）
 - `general_fast`：通用快速版
 - `general_plus`：通用高品質版（目前未附，見 `models/README.md`）


## 安裝

    npm install @plotdb/upscaler @tensorflow/tfjs


## 前端（瀏覽器）使用範例


### 引入依賴

透過 bundler（webpack、vite 等）使用時：

    const tf = require('@tensorflow/tfjs');
    const WebUpscaler = require('@plotdb/upscaler');

透過 CDN 在瀏覽器直接引入時，TensorFlow.js 必須先於 `@plotdb/upscaler` 載入：

    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
    <!-- 可選：WebGPU 後端（Chrome/Edge 113+） -->
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgpu@4.22.0/dist/tf-backend-webgpu.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@plotdb/upscaler/dist/index.min.js"></script>


### 基本使用

    var upscaler = new WebUpscaler({
      modelType: 'realcugan',   // 'realcugan' 或 'realesrgan'
      scale: 4,                  // 2 或 4
      backend: 'webgl',          // 'webgpu'（較快）或 'webgl'（相容性佳）
      modelBaseUrl: '/models'
    });

    // 預載入模型（推薦，避免第一次處理卡頓）
    upscaler.warmup().then(function() {
      return upscaler.upscale(inputBlob, {
        format: 'png',                                    // 'png' | 'jpeg' | 'webp'
        quality: 0.92,                                    // 0-1（僅 jpeg/webp 有效）
        onProgress: function(p) { console.log(p + '%'); } // 進度回調 0-100
      });
    }).then(function(outputBlob) {
      document.getElementById('result').src = URL.createObjectURL(outputBlob);
      upscaler.dispose();
    });


### 從 `<input type="file">` 上傳

HTML 結構：

    <input type="file" id="fileInput" accept="image/*">
    <img id="original">
    <img id="result">

對應的 JavaScript：

    var upscaler = new WebUpscaler({
      modelType: 'realcugan',
      scale: 4,
      backend: 'webgpu',
      modelBaseUrl: '/models'
    });

    document.getElementById('fileInput').addEventListener('change', function(e) {
      var file = e.target.files[0];
      if (!file) return;
      document.getElementById('original').src = URL.createObjectURL(file);
      upscaler.upscale(file, {
        format: 'png',
        onProgress: function(p) { console.log('處理中: ' + p.toFixed(1) + '%'); }
      }).then(function(resultBlob) {
        document.getElementById('result').src = URL.createObjectURL(resultBlob);
      });
    });


### 批次處理多張圖片

    var upscaler = new WebUpscaler({ scale: 4, modelBaseUrl: '/models' });
    var results = [];

    upscaler.warmup().then(function() {
      var files = Array.from(document.getElementById('fileInput').files);
      return files.reduce(function(chain, file, i) {
        return chain.then(function() {
          console.log('處理 ' + (i + 1) + '/' + files.length + ': ' + file.name);
          return upscaler.upscale(file, {
            onProgress: function(p) { console.log('  ' + p.toFixed(0) + '%'); }
          });
        }).then(function(blob) {
          results.push({ name: file.name, blob: blob });
        });
      }, Promise.resolve());
    }).then(function() {
      upscaler.dispose();
    });


### Real-ESRGAN

    var upscaler = new WebUpscaler({
      modelType: 'realesrgan',
      model: 'general_fast', // anime_fast | general_fast；高品質的 anime_plus / general_plus 目前未附，見 models/README.md
      scale: 4,
      backend: 'webgpu',
      modelBaseUrl: '/models'
    });

    upscaler.upscale(inputBlob).then(function(outputBlob) {
      // 使用 outputBlob
    });


## Node.js 環境使用範例

Node.js 版本透過 `@plotdb/upscaler/node` 引入，介面與瀏覽器版相同。
`upscale()` 接受檔案路徑或 Buffer，回傳 Buffer 而非 Blob。


### 安裝依賴

    npm install @plotdb/upscaler @tensorflow/tfjs-node canvas


### 基本使用

    var NodeUpscaler = require('@plotdb/upscaler/node');

    var upscaler = new NodeUpscaler({
      modelType: 'realcugan',
      scale: 4,
      modelBaseUrl: './models'
    });

    upscaler.upscale('./input.jpg', { format: 'png' })
      .then(function(buffer) {
        require('fs').writeFileSync('./output.png', buffer);
        upscaler.dispose();
      })
      .catch(console.error);


### 批次處理（Node.js）

    var fs = require('fs');
    var path = require('path');
    var NodeUpscaler = require('@plotdb/upscaler/node');

    var upscaler = new NodeUpscaler({ scale: 4, modelBaseUrl: './models' });
    var inputDir = './input';
    var outputDir = './output';
    var files = fs.readdirSync(inputDir).filter(function(f) {
      return /\.(jpg|jpeg|png|webp)$/i.test(f);
    });

    upscaler.warmup().then(function() {
      return files.reduce(function(chain, file) {
        return chain.then(function() {
          var input = path.join(inputDir, file);
          var output = path.join(outputDir, path.basename(file, path.extname(file)) + '_4x.png');
          return upscaler.upscale(input, { format: 'png' }).then(function(buffer) {
            fs.writeFileSync(output, buffer);
          });
        });
      }, Promise.resolve());
    }).then(function() {
      upscaler.dispose();
    });


## 自訂輸入輸出與模型載入

`WebUpscaler` 把跟環境有關的三件事放在三個可覆寫的 hook 上，其餘流程共用。
`@plotdb/upscaler/node` 就是只覆寫這三個：

| hook | 預設行為 | 回傳 |
|---|---|---|
| `decode(input)` | Blob 轉 ImageData（有 `document` 用 img + canvas，worker 用 `createImageBitmap` + `OffscreenCanvas`） | `Promise<ImageData>` |
| `encode(imageData, format, quality)` | canvas 轉 Blob | `Promise<Blob>` |
| `loadModel(url, cacheName)` | 先讀 IndexedDB，沒有才下載並寫回快取 | `Promise<GraphModel>` |

例如要改成從自家 CDN 拿模型、不用 IndexedDB：

    class MyUpscaler extends WebUpscaler {
      loadModel(url) { return tf.loadGraphModel(url.replace('/models', 'https://cdn.example.com/models')); }
    }

其他像切塊、混合、進度、取消都在基底類別裡，覆寫 hook 不會影響它們。


## 配置選項速查

`WebUpscaler` 建構子選項：

    new WebUpscaler({
      modelType: 'realcugan',  // 'realcugan' | 'realesrgan'
      scale: 4,                // 2 | 4
      backend: 'webgl',        // 'webgpu' | 'webgl'（僅前端，Node.js 忽略此項）
      modelBaseUrl: '/models', // 模型資料夾路徑
      tileSize: 64,            // tile 大小，預設 64；記憶體不足時可調小
      overlap: 12,             // tile overlap，預設 12
      denoise: 'conservative', // 僅 realcugan：conservative | no-denoise | denoise1x | denoise2x | denoise3x
      model: 'anime_fast',     // 僅 realesrgan：anime_fast | general_fast（anime_plus / general_plus 目前未附）
      margin: 0,               // 混合前先丟棄每個 tile 邊緣幾個像素，需 margin * 2 <= overlap
      sharpen: 0,              // 0-1，對模型輸出做 3x3 銳化後依此比例混合回去
      debug: false,            // true 時把載入與處理進度印到 console
    })

實際放大倍數由模型決定，不是由 `scale` 決定。`scale` 只用來挑 realcugan 的 2x / 4x 模型檔；
realesrgan 固定 4x，所以 `new WebUpscaler({modelType: 'realesrgan', scale: 2})` 仍然會放大 4 倍
（`debug: true` 時會警告）。載入後可以從 `upscaler.modelScale` 讀到實際倍數。

選項給錯值（不存在的 `modelType` / `denoise` / `model`，或 realcugan 4x 配上只有 2x 的
`denoise1x` / `denoise2x`）會在 `new` 的時候就丟出錯誤，不會等到載入模型時才 404。

`upscale()` 選項：

    upscaler.upscale(input, {
      format: 'png',               // 'png' | 'jpeg' | 'webp'
      quality: 0.92,               // 0-1（jpeg/webp）
      onProgress: function(p) {},  // 進度回調，p 為 0-100
      signal: abortController.signal  // 中途取消，見下
    })

`upscaleImageData()` 吃同一組 `onProgress` 與 `signal`。


## 中途取消

`upscale()` 與 `upscaleImageData()` 都接受標準的 `AbortSignal`。每個 tile 處理完會檢查一次，
取消時釋放已配置的 tensor，並以 `AbortError` reject：

    var ac = new AbortController();
    document.getElementById('cancel').onclick = function() { ac.abort(); };

    upscaler.upscale(file, { signal: ac.signal })
      .then(function(blob) { /* ... */ })
      .catch(function(e) {
        if (e.name === 'AbortError') console.log('已取消');
        else throw e;
      });


## 透明度

模型本身只吃 RGB，所以 alpha 通道是另外處理的：

 - 輸入完全不透明時，輸出 alpha 全部是 255，不另外計算。
 - 輸入有半透明或全透明的像素時，alpha 用雙線性內插放大同樣的倍數後放回輸出。
 - 送進模型的 RGB 是原本的值，沒有預乘 alpha，所以全透明區域底下的顏色不會汙染鄰近像素。


## ImageData 進、ImageData 出

來源已經是 `ImageData`（canvas、影片抽格、上一段流程的輸出），而下一步也吃 `ImageData` 時，
用 `upscaleImageData()` 可以省掉 `upscale()` 進出各一次的圖片編解碼：

    var out = await upscaler.upscaleImageData(imageData, {
      onProgress: function(p) {}
    });
    // out 是放大後的 ImageData

這條路徑不碰 DOM。


## 在 Web Worker 裡跑

放大一張圖要好幾秒，跑在主執行緒上整頁都會卡住，建議放進 worker：

    // upscale-worker.js
    importScripts(
      '/assets/lib/@tensorflow/tfjs/main/dist/tf.min.js',
      '/assets/lib/@tensorflow/tfjs-backend-webgpu/main/dist/tf-backend-webgpu.min.js',
      '/assets/lib/@plotdb/upscaler/main/index.min.js'
    );

    var upscaler = new WebUpscaler({
      modelType: 'realcugan', scale: 2, backend: 'webgpu',
      modelBaseUrl: '/assets/lib/@plotdb/upscaler/main/models'
    });
    var ready = upscaler.warmup();

    self.onmessage = function(e) {
      ready
        .then(function() { return upscaler.upscaleImageData(e.data.imageData); })
        // ImageData 的 buffer 用 transfer 交還，不複製
        .then(function(out) { self.postMessage({imageData: out}, [out.data.buffer]); });
    };

worker 裡沒有 `document`，blob 相關的轉換會自動改走 `createImageBitmap` / `OffscreenCanvas`，
所以 `upscale()`（吃 Blob）在 worker 裡一樣可用。


## 注意事項

 - 模型快取：首次使用會下載模型並存入 IndexedDB，後續從快取讀取。
 - WebGPU 需求：需要 Chrome/Edge 113+，且必須在 HTTPS 或 localhost 下運行。worker 裡一樣可用。
 - 記憶體釋放：處理完成後呼叫 `upscaler.dispose()` 釋放 GPU 記憶體。
 - 大圖 OOM：若遇到記憶體不足，將 `tileSize` 縮小（如改為 32）。
 - 小圖：寬或高小於 `tileSize` 時會先用 edge replicate 補到一個 tile 的大小，輸出再裁回 `寬 * 倍數 x 高 * 倍數`，所以 1x1 這種極端尺寸也能跑。
 - Node.js：用 `@plotdb/upscaler/node`（見上），它已經包好 `@tensorflow/tfjs-node` 與 `canvas`，不需要自己 polyfill。
