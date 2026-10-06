// 用同一張圖分別跑兩組模型 ( 例如 xororz 版 vs 自行轉換版 ), 輸出像素差統計與結果圖.
//
// usage:
//   node tools/convert/compare.js --a <modelBaseUrl> --b <modelBaseUrl> --model <spec> --image <file> [--out <dir>]
//
// <spec>: realesrgan/general_fast | realcugan/2x-conservative | realcugan/4x-no-denoise ...
var fs = require('fs');
var path = require('path');
var { createCanvas } = require('canvas');
var NodeUpscaler = require('../../src/node.js');

function arg(name, def) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 ? process.argv[i + 1] : def;
}

function options(spec, base) {
  var [type, name] = spec.split('/');
  if (type === 'realesrgan') return { modelType: type, model: name, scale: 4, modelBaseUrl: base };
  var m = /^(\d)x-(.+)$/.exec(name);
  return { modelType: type, scale: +m[1], denoise: m[2], modelBaseUrl: base };
}

async function run(spec, base, image) {
  var up = new NodeUpscaler(options(spec, base));
  var input = await up._blobToImageData(image);
  var t = Date.now();
  var out = await up.upscaleImageData(input);
  var ms = Date.now() - t;
  up.dispose();
  return { out, ms };
}

function save(imageData, file) {
  var canvas = createCanvas(imageData.width, imageData.height);
  canvas.getContext('2d').putImageData(imageData, 0, 0);
  fs.writeFileSync(file, canvas.toBuffer('image/png'));
}

function stats(a, b) {
  var n = 0, sum = 0, sq = 0, max = 0, over1 = 0, over4 = 0;
  for (var i = 0; i < a.data.length; i++) {
    if (i % 4 === 3) continue;
    var d = Math.abs(a.data[i] - b.data[i]);
    n++; sum += d; sq += d * d;
    if (d > max) max = d;
    if (d > 1) over1++;
    if (d > 4) over4++;
  }
  var mse = sq / n;
  return {
    meanAbs: +(sum / n).toFixed(4),
    max: max,
    psnr: mse === 0 ? Infinity : +(10 * Math.log10(255 * 255 / mse)).toFixed(2),
    'ratio(d>1)': +(over1 / n).toFixed(5),
    'ratio(d>4)': +(over4 / n).toFixed(5)
  };
}

(async function() {
  var a = arg('a'), b = arg('b'), spec = arg('model'), image = arg('image');
  var outdir = arg('out');
  var ra = await run(spec, a, image);
  var rb = await run(spec, b, image);
  var s = stats(ra.out, rb.out);
  var result = Object.assign({ model: spec, image: image, size: ra.out.width + 'x' + ra.out.height, msA: ra.ms, msB: rb.ms }, s);
  console.log(JSON.stringify(result));
  if (outdir) {
    fs.mkdirSync(outdir, { recursive: true });
    var tag = spec.replace('/', '_') + '_' + path.basename(path.dirname(image));
    save(ra.out, path.join(outdir, tag + '_a.png'));
    save(rb.out, path.join(outdir, tag + '_b.png'));
  }
})();
