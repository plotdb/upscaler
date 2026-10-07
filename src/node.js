// Node.js build of WebUpscaler.
//
// Same interface as the browser version, except that `upscale()` takes a file
// path or a Buffer and resolves to a Buffer. Implemented purely through the
// documented hooks: decode / encode / loadModel.

// Polyfill for util.isNullOrUndefined (removed in Node.js 22+)
// Required by @tensorflow/tfjs-node which still uses this deprecated function
const util = require('util');
if (typeof util.isNullOrUndefined !== 'function') {
  util.isNullOrUndefined = function(arg) {
    return arg === null || arg === undefined;
  };
}

const tf = require('@tensorflow/tfjs-node');
const { createCanvas, loadImage, ImageData } = require('canvas');
const path = require('path');

// WebUpscaler uses tf and ImageData as globals
global.tf = tf;
global.ImageData = ImageData;

const WebUpscaler = require('./index.js');

const MIMES = { png: 'image/png', jpeg: 'image/jpeg', jpg: 'image/jpeg', webp: 'image/webp' };

class NodeUpscaler extends WebUpscaler {
  constructor(options = {}) {
    // tfjs-node runs on the native backend; webgl / webgpu don't exist here
    super(Object.assign({}, options, { backend: options.backend || 'tensorflow' }));
  }

  // Hook: accept a file path or a Buffer instead of a Blob
  decode(input) {
    return loadImage(input).then(function(img) {
      var canvas = createCanvas(img.width, img.height);
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      return ctx.getImageData(0, 0, img.width, img.height);
    });
  }

  // Hook: return a Buffer instead of a Blob
  encode(imageData, format, quality) {
    var canvas = createCanvas(imageData.width, imageData.height);
    canvas.getContext('2d').putImageData(imageData, 0, 0);
    var mime = MIMES[format] || MIMES.png;
    return Promise.resolve(canvas.toBuffer(mime, { quality: quality === undefined ? 0.92 : quality }));
  }

  // Hook: no IndexedDB here -- load straight from disk ( or http )
  loadModel(url) {
    if (!/^[a-z]+:\/\//.test(url)) url = 'file://' + path.resolve(url);
    this.log('loading model', url);
    return tf.loadGraphModel(url);
  }
}

module.exports = NodeUpscaler;
