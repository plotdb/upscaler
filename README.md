# @plotdb/upscaler

image upscaler with tf.js, running Real-ESRGAN / Real-CUGAN models converted from their official weights. works in browsers, Web Workers and Node.js.

for usage, check `usage.md`. for model conversion, check `tools/convert/`.

History: versions up to 0.0.3 were based on xororz/web-realesrgan ( https://github.com/xororz/web-realesrgan , GPL ) for both code and converted models. models were replaced in 0.0.4 and the code was rewritten in 0.0.5; neither is derived from it anymore.


## License

Real-CUGAN:
 - https://github.com/bilibili/ailab/blob/main/Real-CUGAN/LICENSE
 - MIT License

Real-ESRGAN:
 - https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE
 - BSD 3-Clause License

Converted models:
 - converted by ourselves from the official PyTorch weights to tf.js, with scripts in `tools/convert/`
 - the converted models keep the license of the original weights ( see `models/README.md`, `models/realesrgan/LICENSE`, `models/realcugan/LICENSE` )
 - Real-ESRGAN `general_plus` / `anime_plus` are not shipped for now; see `models/README.md` for how to convert them
