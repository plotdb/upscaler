#const upscaler = new WebUpscaler({ scale: 4 });
#const resultBlob = await upscaler.upscale(file);
console.log "inited"
view = new ldview do
  root: document.body
  action: change: upload: ({node}) ->
    console.log node.files
    upscale-image file: node.files.0

sample-image = "/assets/img/sample.png"
upscale-image = ({file, url}) ->
  img = new Image!
  img.src = if file => URL.createObjectURL(file) else url or sample-image
  view.get(\img1).textContent = ""
  view.get(\img1).appendChild img
  p = if file => Promise.resolve({file}) else ldfile.fromURL(img.src, \blob)
  <- p.then _

  # Here is the core upscale logic: create an upscaler, call with blob(file), return blob(ret)
  upscale = new WebUpscaler scale: 2, sharpen: 0.2
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
