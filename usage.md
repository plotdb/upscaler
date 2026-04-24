# Web Upscaler 使用範例


## 可用模型一覽

支援兩種模型類型：

 - `realcugan`：Real-CUGAN，支援 2x / 4x 放大，快速，適合動漫，模型小（約 3MB）
 - `realesrgan`：Real-ESRGAN，支援 4x 放大，高品質，適合照片與動漫，模型較大（約 9-34MB）

Real-CUGAN `denoise` 選項：

 - `conservative`：保守降噪（推薦），支援 2x / 4x
 - `no-denoise`：不降噪，支援 2x / 4x
 - `denoise1x`：輕度降噪，僅 2x
 - `denoise2x`：中度降噪，僅 2x
 - `denoise3x`：強力降噪，支援 2x / 4x

Real-ESRGAN `model` 選項：

 - `anime_fast`：動漫快速版
 - `anime_plus`：動漫高品質版
 - `general_fast`：通用快速版
 - `general_plus`：通用高品質版


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
    <script src="https://cdn.jsdelivr.net/npm/@plotdb/upscaler/dist/upscaler.js"></script>


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


### Real-ESRGAN 高品質模式

    var upscaler = new WebUpscaler({
      modelType: 'realesrgan',
      model: 'general_plus', // anime_fast | anime_plus | general_fast | general_plus
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
      model: 'anime_plus',     // 僅 realesrgan：anime_fast | anime_plus | general_fast | general_plus
    })

`upscale()` 選項：

    upscaler.upscale(input, {
      format: 'png',               // 'png' | 'jpeg' | 'webp'
      quality: 0.92,               // 0-1（jpeg/webp）
      onProgress: function(p) {}   // 進度回調，p 為 0-100
    })


## 注意事項

 - 模型快取：首次使用會下載模型並存入 IndexedDB，後續從快取讀取。
 - WebGPU 需求：需要 Chrome/Edge 113+，且必須在 HTTPS 或 localhost 下運行。
 - 記憶體釋放：處理完成後呼叫 `upscaler.dispose()` 釋放 GPU 記憶體。
 - 大圖 OOM：若遇到記憶體不足，將 `tileSize` 縮小（如改為 32）。
 - Node.js 限制：`@plotdb/upscaler` 為純瀏覽器版，Node.js 需自行 polyfill 並使用 `@tensorflow/tfjs-node`。
