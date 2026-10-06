"""
TensorFlow (NHWC) re-implementation of the networks in archs.py, fed with the
PyTorch state dict. Used instead of ONNX -> onnx2tf, which mis-infers layouts
around Real-CUGAN's SE blocks.

Every builder returns `fn(x)` with x: [N, H, W, 3] float32 in 0~1.
"""
import numpy as np
import tensorflow as tf


def _np(state, k):
  return state[k].detach().cpu().numpy().astype(np.float32)


class Conv:
  """nn.Conv2d with padding 0 or 'same'-style symmetric padding p."""
  def __init__(self, state, name, stride=1, pad=0):
    w = _np(state, name + '.weight')                      # (O, I, kh, kw)
    self.w = tf.constant(np.transpose(w, (2, 3, 1, 0)))   # (kh, kw, I, O)
    self.b = tf.constant(_np(state, name + '.bias')) if name + '.bias' in state else None
    self.stride, self.pad = stride, pad

  def __call__(self, x):
    k = self.w.shape[0]
    if self.pad and self.stride == 1 and k == 2 * self.pad + 1:
      y = tf.nn.conv2d(x, self.w, 1, 'SAME')  # same as zero padding p, without a separate Pad op
    else:
      if self.pad: x = tf.pad(x, [[0, 0], [self.pad] * 2, [self.pad] * 2, [0, 0]])
      y = tf.nn.conv2d(x, self.w, self.stride, 'VALID')
    return y if self.b is None else tf.nn.bias_add(y, self.b)


class Deconv:
  """nn.ConvTranspose2d(k, stride, padding=p): full VALID transposed conv, then crop p."""
  def __init__(self, state, name, k, stride, pad):
    w = _np(state, name + '.weight')                      # (I, O, kh, kw)
    self.w = tf.constant(np.transpose(w, (2, 3, 1, 0)))   # (kh, kw, O, I)
    self.b = tf.constant(_np(state, name + '.bias'))
    self.k, self.stride, self.pad = k, stride, pad
    self.cout = w.shape[1]

  def __call__(self, x):
    n, h, w = x.shape[0], x.shape[1], x.shape[2]
    oh, ow = (h - 1) * self.stride + self.k, (w - 1) * self.stride + self.k
    y = tf.nn.conv2d_transpose(x, self.w, [n, oh, ow, self.cout], self.stride, 'VALID')
    if self.pad: y = y[:, self.pad:-self.pad, self.pad:-self.pad, :]
    return tf.nn.bias_add(y, self.b)


def lrelu(x): return tf.nn.leaky_relu(x, 0.1)


def crop(x, p): return x[:, p:-p, p:-p, :]


def pixel_shuffle_perm(c, r):
  """channel permutation turning torch PixelShuffle order (c, i, j) into tf depth_to_space order (i, j, c)."""
  return np.array([ci * r * r + i * r + j for i in range(r) for j in range(r) for ci in range(c)])


# ---------------------------------------------------------------- Real-ESRGAN

def srvgg(state, num_conv=32, upscale=4, num_out_ch=3):
  convs = [Conv(state, f'body.{2 * i}', pad=1) for i in range(num_conv + 2)]
  # stored negated: PReLU is written as relu(x) + (-alpha) * relu(-x), the form
  # tensorflowjs_converter fuses into _FusedConv2D(BiasAdd, Prelu).
  neg_alphas = [tf.constant(-_np(state, f'body.{2 * i + 1}.weight')) for i in range(num_conv + 1)]
  last = convs[-1]
  perm = pixel_shuffle_perm(num_out_ch, upscale)
  last.w = tf.gather(last.w, perm, axis=3)
  last.b = tf.gather(last.b, perm)

  def fn(x):
    out = x
    for conv, na in zip(convs[:-1], neg_alphas):
      out = conv(out)
      out = tf.nn.relu(out) + na * tf.nn.relu(-out)
    out = tf.nn.depth_to_space(last(out), upscale)
    base = tf.image.resize(x, [x.shape[1] * upscale, x.shape[2] * upscale], method='nearest')
    return out + base
  return fn


def rrdbnet(state, num_block=23):
  lrelu2 = lambda t: tf.nn.leaky_relu(t, 0.2)
  up2 = lambda t: tf.image.resize(t, [t.shape[1] * 2, t.shape[2] * 2], method='nearest')
  c = lambda name: Conv(state, name, pad=1)

  def rdb(p):
    convs = [c(f'{p}.conv{i}') for i in range(1, 6)]
    def fn(x):
      feats = [x]
      for conv in convs[:-1]: feats.append(lrelu2(conv(tf.concat(feats, axis=3))))
      return convs[-1](tf.concat(feats, axis=3)) * 0.2 + x
    return fn

  blocks = [[rdb(f'body.{b}.rdb{i}') for i in (1, 2, 3)] for b in range(num_block)]
  first, body, up1, up2c, hr, last = (
    c('conv_first'), c('conv_body'), c('conv_up1'), c('conv_up2'), c('conv_hr'), c('conv_last'))

  def fn(x):
    feat = first(x)
    out = feat
    for r1, r2, r3 in blocks: out = r3(r2(r1(out))) * 0.2 + out
    feat = feat + body(out)
    feat = lrelu2(up1(up2(feat)))
    feat = lrelu2(up2c(up2(feat)))
    return last(lrelu2(hr(feat)))
  return fn


# ---------------------------------------------------------------- Real-CUGAN

def se_block(state, name):
  c1, c2 = Conv(state, name + '.conv1'), Conv(state, name + '.conv2')
  def fn(x):
    x0 = tf.reduce_mean(x, axis=[1, 2], keepdims=True)
    return x * tf.sigmoid(c2(tf.nn.relu(c1(x0))))
  return fn


def unet_conv(state, name, se):
  c1, c2 = Conv(state, name + '.conv.0'), Conv(state, name + '.conv.2')
  s = se_block(state, name + '.seblock') if se else None
  def fn(x):
    z = lrelu(c2(lrelu(c1(x))))
    return s(z) if s else z
  return fn


def bottom(state, name, deconv):
  return Deconv(state, name, 4, 2, 3) if deconv else Conv(state, name)


def unet1(state, p, deconv):
  conv1, conv2 = unet_conv(state, p + 'conv1', False), unet_conv(state, p + 'conv2', True)
  down, up = Conv(state, p + 'conv1_down', stride=2), Deconv(state, p + 'conv2_up', 2, 2, 0)
  conv3, bot = Conv(state, p + 'conv3'), bottom(state, p + 'conv_bottom', deconv)
  def fn(x):
    x1 = conv1(x)
    x2 = lrelu(down(x1))
    x1 = crop(x1, 4)
    x2 = lrelu(up(conv2(x2)))
    return bot(lrelu(conv3(x1 + x2)))
  return fn


def unet2(state, p, deconv):
  conv1, conv2 = unet_conv(state, p + 'conv1', False), unet_conv(state, p + 'conv2', True)
  conv3, conv4 = unet_conv(state, p + 'conv3', True), unet_conv(state, p + 'conv4', True)
  down1, down2 = Conv(state, p + 'conv1_down', stride=2), Conv(state, p + 'conv2_down', stride=2)
  up3, up4 = Deconv(state, p + 'conv3_up', 2, 2, 0), Deconv(state, p + 'conv4_up', 2, 2, 0)
  conv5, bot = Conv(state, p + 'conv5'), bottom(state, p + 'conv_bottom', deconv)
  def fn(x):
    x1 = conv1(x)
    x2 = lrelu(down1(x1))
    x1 = crop(x1, 16)
    x2 = conv2(x2)
    x3 = lrelu(down2(x2))
    x2 = crop(x2, 4)
    x3 = lrelu(up3(conv3(x3)))
    x4 = lrelu(up4(conv4(x2 + x3)))
    return bot(lrelu(conv5(x1 + x4)))
  return fn


def reflect(x, p): return tf.pad(x, [[0, 0], [p, p], [p, p], [0, 0]], mode='REFLECT')


def upcunet2x(state):
  u1, u2 = unet1(state, 'unet1.', True), unet2(state, 'unet2.', False)
  def fn(x):
    x = u1(reflect(x, 18))
    return u2(x) + crop(x, 20)
  return fn


def upcunet4x(state):
  u1, u2 = unet1(state, 'unet1.', True), unet2(state, 'unet2.', False)
  final = Conv(state, 'conv_final')
  perm = pixel_shuffle_perm(3, 2)
  final.w = tf.gather(final.w, perm, axis=3)
  final.b = tf.gather(final.b, perm)
  def fn(x):
    x00 = x
    x = u1(reflect(x, 19))
    x = crop(final(u2(x) + crop(x, 20)), 1)
    x = tf.nn.depth_to_space(x, 2)
    return x + tf.image.resize(x00, [x00.shape[1] * 4, x00.shape[2] * 4], method='nearest')
  return fn
