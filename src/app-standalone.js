/**
 * Web Upscaler - UI 應用
 * 使用 upscaler.js 提供的 WebUpscaler 類
 */

// ============================================
// 全局變量
// ============================================

let upscaler = null;
let currentFile = null;
let resultBlob = null;

// ============================================
// DOM 元素
// ============================================

const elements = {
  uploadArea: document.getElementById('uploadArea'),
  fileInput: document.getElementById('fileInput'),
  modelType: document.getElementById('modelType'),
  scale: document.getElementById('scale'),
  backend: document.getElementById('backend'),
  processBtn: document.getElementById('processBtn'),
  downloadBtn: document.getElementById('downloadBtn'),
  progressContainer: document.getElementById('progressContainer'),
  progressFill: document.getElementById('progressFill'),
  statusText: document.getElementById('statusText'),
  resultContainer: document.getElementById('resultContainer'),
  originalImg: document.getElementById('originalImg'),
  upscaledImg: document.getElementById('upscaledImg'),
  originalInfo: document.getElementById('originalInfo'),
  upscaledInfo: document.getElementById('upscaledInfo'),
  error: document.getElementById('error')
};

// ============================================
// UI 事件處理
// ============================================

/**
 * 文件上傳
 */
elements.fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) handleFile(file);
});

elements.uploadArea.addEventListener('click', () => {
  elements.fileInput.click();
});

elements.uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  elements.uploadArea.classList.add('drag-over');
});

elements.uploadArea.addEventListener('dragleave', () => {
  elements.uploadArea.classList.remove('drag-over');
});

elements.uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  elements.uploadArea.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    handleFile(file);
  }
});

/**
 * 處理文件
 */
function handleFile(file) {
  currentFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    elements.originalImg.src = e.target.result;

    const img = new Image();
    img.onload = () => {
      elements.originalInfo.textContent = `${img.width} × ${img.height}`;
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);

  elements.processBtn.disabled = false;
  elements.resultContainer.classList.remove('active');
  elements.downloadBtn.disabled = true;
  hideError();
}

/**
 * 開始處理
 */
elements.processBtn.addEventListener('click', async () => {
  if (!currentFile) return;

  try {
    elements.processBtn.disabled = true;
    elements.downloadBtn.disabled = true;
    showProgress();
    updateProgress(0, '初始化...');

    // 創建 upscaler 實例（根據當前設置）
    const selectedOption = elements.modelType.options[elements.modelType.selectedIndex];
    const modelType = selectedOption.value;
    const scale = parseInt(elements.scale.value);
    const backend = elements.backend.value;

    const config = {
      modelType,
      scale,
      backend,
      modelBaseUrl: '/models'
    };

    // 根據模型類型添加額外配置
    if (modelType === 'realcugan') {
      config.denoise = selectedOption.dataset.denoise || 'conservative';
    } else if (modelType === 'realesrgan') {
      config.model = selectedOption.dataset.model || 'anime_fast';
    }

    upscaler = new WebUpscaler(config);

    // 預載入模型
    updateProgress(10, '載入模型...');
    await upscaler.warmup();

    // 處理圖片
    updateProgress(20, '處理圖片...');
    resultBlob = await upscaler.upscale(currentFile, {
      format: 'png',
      quality: 0.92,
      onProgress: (progress) => {
        // 進度從 20% 到 90%
        const uiProgress = 20 + (progress / 100) * 70;
        updateProgress(uiProgress, `處理中... ${Math.round(progress)}%`);
      }
    });

    // 顯示結果
    updateProgress(95, '生成預覽...');
    const url = URL.createObjectURL(resultBlob);
    elements.upscaledImg.src = url;

    const img = new Image();
    img.onload = () => {
      elements.upscaledInfo.textContent = `${img.width} × ${img.height}`;
      updateProgress(100, '完成！');

      setTimeout(() => {
        hideProgress();
        elements.resultContainer.classList.add('active');
        elements.downloadBtn.disabled = false;
        elements.processBtn.disabled = false;
      }, 500);
    };
    img.src = url;

  } catch (error) {
    console.error('處理失敗:', error);
    showError(`處理失敗: ${error.message}`);
    hideProgress();
    elements.processBtn.disabled = false;
  }
});

/**
 * 下載結果
 */
elements.downloadBtn.addEventListener('click', () => {
  if (!resultBlob) return;

  const url = URL.createObjectURL(resultBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `upscaled_${Date.now()}.png`;
  a.click();
  URL.revokeObjectURL(url);
});

/**
 * 設置變更時提示
 */
['modelType', 'scale', 'backend'].forEach(id => {
  elements[id].addEventListener('change', () => {
    if (upscaler) {
      // 設置改變了，需要重新創建 upscaler
      upscaler.dispose();
      upscaler = null;
    }

    if (currentFile) {
      elements.resultContainer.classList.remove('active');
      elements.downloadBtn.disabled = true;
    }
  });
});

// ============================================
// UI 輔助函數
// ============================================

function showProgress() {
  elements.progressContainer.classList.add('active');
}

function hideProgress() {
  elements.progressContainer.classList.remove('active');
}

function updateProgress(percent, status) {
  const p = Math.round(percent);
  elements.progressFill.style.width = `${p}%`;
  elements.progressFill.textContent = `${p}%`;
  elements.statusText.textContent = status;
}

function showError(message) {
  elements.error.textContent = message;
  elements.error.classList.add('active');
}

function hideError() {
  elements.error.classList.remove('active');
}

// ============================================
// 快捷鍵
// ============================================

document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + O: 打開文件
  if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
    e.preventDefault();
    elements.fileInput.click();
  }

  // Ctrl/Cmd + Enter: 開始處理
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    if (!elements.processBtn.disabled) {
      elements.processBtn.click();
    }
  }

  // Ctrl/Cmd + S: 下載結果
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    if (!elements.downloadBtn.disabled) {
      elements.downloadBtn.click();
    }
  }
});

// ============================================
// 頁面載入完成
// ============================================

window.addEventListener('load', () => {
  console.log('Web Upscaler 已準備好');
  console.log('快捷鍵：Ctrl+O 打開, Ctrl+Enter 處理, Ctrl+S 下載');

  // 檢查 TensorFlow.js 是否載入
  if (typeof tf === 'undefined') {
    showError('TensorFlow.js 載入失敗，請檢查網路連接');
  }
});

// 清理資源
window.addEventListener('beforeunload', () => {
  if (upscaler) {
    upscaler.dispose();
  }
});
