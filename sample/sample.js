var NodeUpscaler = require('../src/node.js');
var fs = require('fs');
var upscaler = new NodeUpscaler({
  modelType: 'realcugan',
  scale: 4,
  modelBaseUrl: '../models',
  sharpen: 0.5
});
upscaler.upscale('./sample.png', { format: 'png' })
  .then(function(buffer) {
    fs.writeFileSync('./sample_4x.png', buffer);
    console.log('done: sample_4x.png');
    upscaler.dispose();
  })
  .catch(console.error);
