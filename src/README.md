# Web Upscaler - CDN 版本（獨立運行）

## ✨ 這個版本可以直接運行！

這是一個完全獨立的版本，不需要任何構建工具或 npm 安裝。

### 🚀 立即開始

```bash
cd /workspace/web-upscaler
python3 -m http.server 8000
```

然後訪問：
```
http://localhost:8000/examples/cdn/index.html
```

就這麼簡單！🎉

## 📦 包含內容

- `index.html` - 完整的 UI 界面
- `upscaler.js` - 核心 WebUpscaler 類（可獨立使用）
- `app-standalone.js` - UI 應用邏輯
- `USAGE.md` - API 使用指南

## 🔧 技術實現

### 模組化設計

**upscaler.js** - 核心類：
```javascript
class WebUpscaler {
  async upscale(inputBlob, options) {
    // 輸入 blob，返回 upscaled blob
  }
}
```

**app-standalone.js** - UI 應用：
```javascript
const upscaler = new WebUpscaler({ scale: 4 });
const resultBlob = await upscaler.upscale(file);
```

### 使用 CDN 載入 TensorFlow.js

```html
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-backend-webgpu@4.22.0/dist/tf-backend-webgpu.min.js"></script>
<script src="./upscaler.js"></script>
```

### API 使用範例

```javascript
// 創建實例
const upscaler = new WebUpscaler({
  modelType: 'realcugan',
  scale: 4,
  backend: 'webgpu',
  modelBaseUrl: '/models'
});

// 處理圖片
const outputBlob = await upscaler.upscale(inputBlob, {
  format: 'png',
  onProgress: (p) => console.log(`${p}%`)
});
```

詳細 API 說明請查看 [USAGE.md](./USAGE.md)

## ⚡ 功能

✅ **完整功能** - 與構建版本相同的功能
✅ **無需構建** - 直接在瀏覽器中運行
✅ **獨立運行** - 不依賴 npm 或構建工具
✅ **模型緩存** - 使用 IndexedDB 緩存
✅ **進度顯示** - 實時處理進度
✅ **拖放上傳** - 支持拖放和點擊上傳

## 🆚 與 simple 版本的區別

| 特性 | simple 版本 | cdn 版本 |
|------|-------------|----------|
| 需要構建 | ✅ 需要 | ❌ 不需要 |
| 使用方式 | import from dist | CDN 載入 |
| 依賴管理 | npm | 無 |
| 文件大小 | 較大 | 較小 |
| 適用場景 | 開發項目 | 快速測試/演示 |

## 💡 使用建議

### 適合使用 CDN 版本的情況：

- ✅ 快速測試功能
- ✅ 演示或原型
- ✅ 不想設置構建環境
- ✅ 一次性使用

### 適合使用構建版本的情況：

- ✅ 生產環境
- ✅ 需要離線使用
- ✅ 需要自定義構建
- ✅ 整合到現有項目

## 🐛 問題排查

### 1. TensorFlow.js 載入失敗

**症狀**：控制台錯誤 "tf is not defined"

**解決**：
- 檢查網路連接
- 確保 CDN 可訪問
- 嘗試其他 CDN（如 unpkg）

### 2. CORS 錯誤

**症狀**：無法載入模型

**解決**：
- 使用 `http://localhost` 而不是 `127.0.0.1`
- 確保使用 HTTP 服務器（不要直接用 file://）
- 檢查瀏覽器控制台的錯誤訊息

### 3. 上傳按鈕沒反應

**症狀**：點擊上傳沒有效果

**可能原因**：
1. JavaScript 載入失敗 - 檢查控制台錯誤
2. TensorFlow.js 未載入 - 檢查網路
3. 瀏覽器不支持 - 使用 Chrome/Edge

**解決步驟**：
1. 打開瀏覽器開發者工具（F12）
2. 查看 Console 標籤是否有錯誤
3. 查看 Network 標籤確認 JS 文件已載入
4. 刷新頁面重試

## 📊 性能

- **首次載入**：需要下載 TensorFlow.js (~2MB) + 模型 (~3-30MB)
- **後續使用**：從緩存載入，很快
- **處理速度**：與構建版本相同

## 🔗 CDN 選擇

### 預設（jsDelivr）
```html
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
```

### 替代方案 1（unpkg）
```html
<script src="https://unpkg.com/@tensorflow/tfjs@4.22.0/dist/tf.min.js"></script>
```

### 替代方案 2（cdnjs）
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/tensorflow/4.22.0/tf.min.js"></script>
```

## 📝 修改模型 URL

**默認使用本地模型**：

```javascript
// app-standalone.js 第 12 行
const MODEL_BASE_URL = '/models';  // 使用本地模型
```

如需使用在線 CDN 模型（需要網路且可能有 CORS 問題）：

```javascript
const MODEL_BASE_URL = 'https://upscale.chino.icu';  // 使用在線模型
```

## 🎯 下一步

1. **測試功能** - 上傳圖片試試
2. **調整設置** - 嘗試不同模型和放大倍數
3. **查看代碼** - app-standalone.js 有詳細註解
4. **整合到項目** - 複製代碼到你的項目中

## 📚 相關文檔

- [快速開始指南](../../QUICKSTART.md)
- [模型獲取指南](../../MODELS.md)
- [完整文檔](../../README.md)

---

**這是最簡單的使用方式！** 不需要安裝任何東西，直接運行即可。🚀
