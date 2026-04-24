const tf = require('@tensorflow/tfjs-node');
const { createCanvas, loadImage, ImageData } = require('canvas');
const path = require('path');

// WebUpscaler uses tf and ImageData as globals
global.tf = tf;
global.ImageData = ImageData;

const WebUpscaler = require('./upscaler.js');

class NodeUpscaler extends WebUpscaler {
  constructor(options = {}) {
    super(options);
    // Node.js uses the native tfjs-node backend; webgl/webgpu are not available
    this.backend = 'tensorflow';
  }

  // Override: accept file path or Buffer instead of Blob
  _blobToImageData(input) {
    return loadImage(input).then(function(img) {
      var canvas = createCanvas(img.width, img.height);
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      return ctx.getImageData(0, 0, img.width, img.height);
    });
  }

  // Override: return Buffer instead of Blob
  _imageDataToBlob(imageData, format, quality) {
    format = format || 'png';
    quality = quality || 0.92;
    var canvas = createCanvas(imageData.width, imageData.height);
    var ctx = canvas.getContext('2d');
    ctx.putImageData(imageData, 0, 0);
    var mime = format === 'jpeg' ? 'image/jpeg' : format === 'webp' ? 'image/webp' : 'image/png';
    return Promise.resolve(canvas.toBuffer(mime, { quality: quality }));
  }

  // Override: skip IndexedDB cache, load model directly via file:// or http
  _loadModel() {
    var modelUrl;
    if (this.modelType === 'realesrgan') {
      modelUrl = this.modelBaseUrl + '/realesrgan/' + this.model + '-' + this.tileSize + '/model.json';
    } else {
      modelUrl = this.modelBaseUrl + '/realcugan/' + this.scale + 'x-' + this.denoise + '-' + this.tileSize + '/model.json';
    }
    if (!modelUrl.startsWith('http')) {
      modelUrl = 'file://' + path.resolve(modelUrl);
    }
    return tf.loadGraphModel(modelUrl);
  }
}

module.exports = NodeUpscaler;
