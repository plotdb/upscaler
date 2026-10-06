"""
Convert official Real-ESRGAN / Real-CUGAN PyTorch weights to tf.js graph models.

  PyTorch (.pth) -> TensorFlow SavedModel -> tf.js graph model

The PyTorch weights are loaded into the reference nets in archs.py, copied into
the NHWC TensorFlow re-implementation in tf_archs.py, and the two are checked to
produce the same output before exporting. ( ONNX -> onnx2tf was tried first but
mis-infers layouts around Real-CUGAN's SE blocks. )

Output layout matches models/<type>/<name>-<tile>/ used by WebUpscaler:
  input  `input:0`    float32 [1, tile, tile, 3]          (NHWC, RGB, 0~1)
  output `Identity:0` float32 [1, tile*s, tile*s, 3]      (not clamped)

usage:
  python convert.py <model-key> [<model-key> ...] [--weights DIR] [--out DIR] [--tile 64] [--no-fp16]
  python convert.py --list
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

import numpy as np
import tensorflow as tf
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archs import SRVGGNetCompact, RRDBNet, UpCunet2x, UpCunet4x
import tf_archs

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

ESRGAN_URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/'
CUGAN_URL = 'https://github.com/bilibili/ailab/releases/download/Real-CUGAN/updated_weights.zip'

# key: (weights, torch net builder, tf builder, source urls)
#   weights: a file name, or [(file name, ratio), ...] blended by network interpolation (DNI).
# general_fast blends x4v3 and wdn-x4v3 at 0.5, same as Real-ESRGAN's default `-dn 0.5`
# ( and same as the previously used xororz conversion ).
SRVGG = (lambda: SRVGGNetCompact(num_feat=64, num_conv=32, upscale=4), tf_archs.srvgg)
SRVGG16 = (lambda: SRVGGNetCompact(num_feat=64, num_conv=16, upscale=4), lambda s: tf_archs.srvgg(s, num_conv=16))
RRDB23 = (lambda: RRDBNet(num_block=23), lambda s: tf_archs.rrdbnet(s, num_block=23))
RRDB6 = (lambda: RRDBNet(num_block=6), lambda s: tf_archs.rrdbnet(s, num_block=6))
CU2X = (UpCunet2x, tf_archs.upcunet2x)
CU4X = (UpCunet4x, tf_archs.upcunet4x)
MODELS = {
  'realesrgan/general_fast': (
    [('realesr-general-x4v3.pth', 0.5), ('realesr-general-wdn-x4v3.pth', 0.5)], *SRVGG,
    [ESRGAN_URL + 'realesr-general-x4v3.pth', ESRGAN_URL + 'realesr-general-wdn-x4v3.pth']),
  'realesrgan/anime_fast': ('realesr-animevideov3.pth', *SRVGG16, [ESRGAN_URL + 'realesr-animevideov3.pth']),
  # not shipped in models/ ( weights are large ), see models/README.md
  'realesrgan/general_plus': (
    'RealESRGAN_x4plus.pth', *RRDB23, ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth']),
  'realesrgan/anime_plus': (
    'RealESRGAN_x4plus_anime_6B.pth', *RRDB6,
    ['https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth']),
  'realcugan/2x-conservative': ('up2x-latest-conservative.pth', *CU2X, [CUGAN_URL]),
  'realcugan/2x-no-denoise': ('up2x-latest-no-denoise.pth', *CU2X, [CUGAN_URL]),
  'realcugan/2x-denoise1x': ('up2x-latest-denoise1x.pth', *CU2X, [CUGAN_URL]),
  'realcugan/2x-denoise2x': ('up2x-latest-denoise2x.pth', *CU2X, [CUGAN_URL]),
  'realcugan/2x-denoise3x': ('up2x-latest-denoise3x.pth', *CU2X, [CUGAN_URL]),
  'realcugan/4x-conservative': ('up4x-latest-conservative.pth', *CU4X, [CUGAN_URL]),
  'realcugan/4x-no-denoise': ('up4x-latest-no-denoise.pth', *CU4X, [CUGAN_URL]),
  'realcugan/4x-denoise3x': ('up4x-latest-denoise3x.pth', *CU4X, [CUGAN_URL]),
}


def load_state(path):
  state = torch.load(path, map_location='cpu', weights_only=True)
  if 'params_ema' in state: state = state['params_ema']
  elif 'params' in state: state = state['params']
  return {k: v for k, v in state.items() if k != 'pro'}


def load_net(key, weights_dir):
  """returns (torch reference net, merged state dict)"""
  weights, build, _, _ = MODELS[key]
  if isinstance(weights, str): weights = [(weights, 1.0)]
  states = [(load_state(os.path.join(weights_dir, f)), r) for f, r in weights]
  state = {k: sum(s[k] * r for s, r in states) for k in states[0][0]}
  net = build()
  net.load_state_dict(state, strict=True)
  return net.eval(), state


def run(cmd):
  print('$', ' '.join(cmd))
  subprocess.run(cmd, check=True)


def build_tf(key, weights_dir, tile):
  net, state = load_net(key, weights_dir)
  fn = MODELS[key][2](state)
  # sanity check: TF re-implementation must match the PyTorch reference.
  x = np.random.default_rng(0).random((1, tile, tile, 3), dtype=np.float32)
  with torch.no_grad():
    ref = net(torch.from_numpy(x).permute(0, 3, 1, 2)).permute(0, 2, 3, 1).numpy()
  out = fn(tf.constant(x)).numpy()
  err = np.abs(out - ref).max()
  print(f'{key}: output {out.shape}, max |tf - torch| = {err:.2e}')
  assert out.shape == ref.shape and err < 1e-3, err

  class Model(tf.Module):
    @tf.function(input_signature=[tf.TensorSpec([1, tile, tile, 3], tf.float32, name='input')])
    def serve(self, x):
      return {'output': fn(x)}
  return Model()


def convert(key, weights_dir, out_root, tile, fp16, keep):
  outdir = os.path.join(out_root, f'{key}-{tile}')
  model = build_tf(key, weights_dir, tile)
  work = tempfile.mkdtemp(prefix='upscaler-convert-')
  try:
    saved = os.path.join(work, 'saved_model')
    tf.saved_model.save(model, saved, signatures={'serving_default': model.serve})
    if os.path.exists(outdir): shutil.rmtree(outdir)
    cmd = [
      sys.executable, '-m', 'tensorflowjs.converters.converter',
      '--input_format=tf_saved_model', '--output_format=tfjs_graph_model',
      '--signature_name=serving_default', '--saved_model_tags=serve',
      '--weight_shard_size_bytes=67108864',
    ]
    if fp16: cmd.append('--quantize_float16=*')
    run(cmd + [saved, outdir])
    check_signature(outdir, tile)
    if keep: shutil.copytree(saved, outdir + '.saved_model', dirs_exist_ok=True)
  finally:
    shutil.rmtree(work, ignore_errors=True)
  return outdir


def check_signature(outdir, tile):
  sig = json.load(open(os.path.join(outdir, 'model.json')))['signature']
  i, o = list(sig['inputs'].values())[0], list(sig['outputs'].values())[0]
  dims = lambda t: [int(d['size']) for d in t['tensorShape']['dim']]
  print('signature:', i['name'], dims(i), '->', o['name'], dims(o))
  assert i['name'] == 'input:0' and dims(i) == [1, tile, tile, 3], i
  assert o['name'] == 'Identity:0' and dims(o)[0] == 1 and dims(o)[3] == 3, o


def main():
  p = argparse.ArgumentParser()
  p.add_argument('models', nargs='*')
  p.add_argument('--list', action='store_true')
  p.add_argument('--weights', default=os.path.join(ROOT, 'tools', 'convert', 'weights'))
  p.add_argument('--out', default=os.path.join(ROOT, 'models'))
  p.add_argument('--tile', type=int, default=64)
  p.add_argument('--no-fp16', action='store_true')
  p.add_argument('--keep', action='store_true', help='keep the intermediate saved_model next to output')
  a = p.parse_args()
  if a.list or not a.models:
    for k, (w, _, _, urls) in MODELS.items(): print(f'{k:28s} {w}\n{"":28s} {" ".join(urls)}')
    return
  for k in a.models:
    print(convert(k, a.weights, a.out, a.tile, not a.no_fp16, a.keep))


if __name__ == '__main__':
  main()
