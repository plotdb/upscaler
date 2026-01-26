#const upscaler = new WebUpscaler({ scale: 4 });
#const resultBlob = await upscaler.upscale(file);
console.log "inited"
view = new ldview root: document.body

sample-image = "/assets/img/sample.png"
img = new Image!
img.src = sample-image
view.get(\img1).appendChild img

upscale = new WebUpscaler scale: 4
({result, file}) <- ldfile.fromURL sample-image, \blob .then _
(ret) <- upscale.upscale file, {format: \jpg, progress: (->console.log it)} .then _
img = new Image!
img.src = URL.createObjectURL ret
view.get(\img2).textContent = ''
view.get(\img2).appendChild img


/* upscaler option sample:

    modelType: 'realcugan',
    scale: 4,
    backend: 'webgpu',
    modelBaseUrl: '/models'

*/
