# Upscaler.js 使用指南

## 簡介

`upscaler.js` 提供了一個簡單的 API，讓你可以在瀏覽器中輕鬆放大圖片。

**核心功能**：輸入圖片 Blob → 返回放大後的圖片 Blob


## 快速開始

### 1. 引入依賴

```html
<!-- TensorFlow.js -->
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgpu@4.22.0/dist/tf-backend-webgpu.min.js"></script>

<!-- Upscaler -->
<script src="./upscaler.js"></script>
```


### 2. 基本使用

```javascript
// 創建 upscaler 實例
const upscaler = new WebUpscaler({
  modelType: 'realcugan',  // 'realcugan' 或 'realesrgan'
  scale: 4,                 // 2 或 4
  backend: 'webgpu',        // 'webgpu' 或 'webgl'
  modelBaseUrl: '/models'   // 模型存放位置
});

// 預載入模型（可選但推薦）
await upscaler.warmup();

// 處理圖片
const inputBlob = /* 你的圖片 blob */;
const outputBlob = await upscaler.upscale(inputBlob, {
  format: 'png',      // 'png', 'jpeg', 'webp'
  quality: 0.92,      // 0-1（僅 jpeg/webp）
  onProgress: (p) => console.log(`進度: ${p}%`)
});

// 使用結果
const url = URL.createObjectURL(outputBlob);
img.src = url;

// 清理資源（完成後）
upscaler.dispose();
```


## API 詳解

### WebUpscaler 類

#### 構造函數

    new WebUpscaler(options)

**參數：**

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `modelType` | string | `'realcugan'` | 模型類型：`'realcugan'` 或 `'realesrgan'` |
| `scale` | number | `4` | 放大倍數：`2` 或 `4` |
| `backend` | string | `'webgl'` | 運算後端：`'webgpu'` 或 `'webgl'` |
| `modelBaseUrl` | string | `'/models'` | 模型基礎 URL |
| `tileSize` | number | `64` | Tile 大小（32-512） |
| `overlap` | number | `12` | Overlap 大小 |
| `denoise` | string | `'conservative'` | Real-CUGAN 降噪級別 |
| `model` | string | `'anime_plus'` | Real-ESRGAN 模型名稱 |


#### 方法

##### warmup()

預載入模型。

    await upscaler.warmup();

**返回：** `Promise<void>`


##### upscale(inputBlob, options)

放大圖片。

```javascript
const outputBlob = await upscaler.upscale(inputBlob, {
  format: 'png',
  quality: 0.92,
  onProgress: (progress) => console.log(progress)
});
```

**參數：**

- `inputBlob` (Blob): 輸入圖片 blob
- `options` (Object): 選項
  - `format` (string): 輸出格式 `'png'` | `'jpeg'` | `'webp'`，預設 `'png'`
  - `quality` (number): 輸出質量 0-1，預設 `0.92`（僅 jpeg/webp）
  - `onProgress` (Function): 進度回調，參數為 0-100

**返回：** `Promise<Blob>` - 放大後的圖片 blob


##### dispose()

釋放資源。

    upscaler.dispose();


## 使用範例

### 範例 1：從文件上傳

```javascript
// HTML
<input type="file" id="fileInput" accept="image/*">
<img id="result">

// JavaScript
const upscaler = new WebUpscaler({
  modelType: 'realcugan',
  scale: 4,
  backend: 'webgpu',
  modelBaseUrl: '/models'
});

document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  // 預載入模型
  await upscaler.warmup();

  // 放大圖片
  const resultBlob = await upscaler.upscale(file, {
    format: 'png',
    onProgress: (p) => console.log(`處理中: ${p}%`)
  });

  // 顯示結果
  const url = URL.createObjectURL(resultBlob);
  document.getElementById('result').src = url;
});
```


### 範例 2：從 URL 載入

```javascript
// 從 URL 取得 blob
async function fetchImageBlob(url) {
  const response = await fetch(url);
  return await response.blob();
}

// 使用
const upscaler = new WebUpscaler({ scale: 4 });
await upscaler.warmup();

const inputBlob = await fetchImageBlob('https://example.com/image.jpg');
const outputBlob = await upscaler.upscale(inputBlob);

// 下載結果
const a = document.createElement('a');
a.href = URL.createObjectURL(outputBlob);
a.download = 'upscaled.png';
a.click();
```


### 範例 3：批次處理

```javascript
const upscaler = new WebUpscaler({ scale: 4 });
await upscaler.warmup();

const files = [...document.getElementById('fileInput').files];
const results = [];

for (let i = 0; i < files.length; i++) {
  console.log(`處理 ${i + 1}/${files.length}`);

  const outputBlob = await upscaler.upscale(files[i], {
    onProgress: (p) => console.log(`  進度: ${p}%`)
  });

  results.push(outputBlob);
}

console.log('全部完成！');
upscaler.dispose();
```


### 範例 4：不同配置

```javascript
// 配置 1: 快速處理（Real-CUGAN + WebGPU）
const fastUpscaler = new WebUpscaler({
  modelType: 'realcugan',
  scale: 4,
  backend: 'webgpu'
});

// 配置 2: 高質量（Real-ESRGAN + WebGPU）
const qualityUpscaler = new WebUpscaler({
  modelType: 'realesrgan',
  model: 'anime_fast',
  scale: 4,
  backend: 'webgpu'
});

// 配置 3: 相容性（WebGL）
const compatUpscaler = new WebUpscaler({
  modelType: 'realcugan',
  scale: 4,
  backend: 'webgl'
});
```


## 模型選擇

### Real-CUGAN (推薦)

**優點：**

- 速度快（5-10倍於 Real-ESRGAN）
- 模型小（~3MB）
- 適合動漫圖片

**缺點：**

- 質量略低於 Real-ESRGAN

**使用場景：**

- 需要快速處理
- 動漫圖片
- 實時預覽


### Real-ESRGAN

**優點：**

- 質量高
- 適合真實照片和動漫

**缺點：**

- 速度慢
- 模型大（9-34MB）

**使用場景：**

- 追求最高質量
- 處理真實照片
- 不在意處理時間


## 後端選擇

### WebGPU (推薦)

**優點：**

- 速度快（約 2倍於 WebGL）
- 性能最佳

**缺點：**

- 瀏覽器支持較少（Chrome/Edge 113+）
- 需要 HTTPS 或 localhost


### WebGL

**優點：**

- 廣泛支持
- 所有現代瀏覽器都可用

**缺點：**

- 速度較慢


## 注意事項

1. **首次載入**：首次使用會下載模型到緩存（~3-30MB），後續使用會從緩存載入
2. **記憶體**：處理大圖片需要較多記憶體，建議調小 `tileSize` 如果遇到問題
3. **HTTPS**：WebGPU 需要 HTTPS 或 localhost
4. **資源清理**：處理完成後調用 `dispose()` 釋放資源


## 疑難排解

### 錯誤：tf is not defined

**原因**：TensorFlow.js 未載入

**解決**：確保在 upscaler.js 之前載入 TensorFlow.js

```html
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
<script src="./upscaler.js"></script>
```


### 錯誤：WebGPU is not supported

**原因**：瀏覽器不支持 WebGPU

**解決**：切換到 WebGL 後端

    const upscaler = new WebUpscaler({ backend: 'webgl' });


### 處理速度慢

**解決方案：**

1. 使用 WebGPU 代替 WebGL
2. 使用 Real-CUGAN 代替 Real-ESRGAN
3. 減小圖片尺寸
4. 使用 2x 代替 4x


## 完整範例

查看 `index.html` 和 `app-standalone.js` 獲取完整的 UI 應用範例。


## License

MIT
