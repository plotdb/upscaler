"""
Network definitions used for conversion.

Only the plain (non-tiled) inference path is kept; layer names match the
official checkpoints so `load_state_dict(strict=True)` works.

- SRVGGNetCompact: from Real-ESRGAN (BSD-3-Clause, Copyright (c) 2021, Xintao Wang)
  https://github.com/xinntao/Real-ESRGAN/blob/master/realesrgan/archs/srvgg_arch.py
- RRDBNet (x4 only): from BasicSR, used by Real-ESRGAN x4plus models (Apache-2.0)
  https://github.com/XPixelGroup/BasicSR/blob/master/basicsr/archs/rrdbnet_arch.py
- UpCunet2x / UpCunet4x: from Real-CUGAN (MIT, Copyright (c) 2022 bilibili)
  https://github.com/bilibili/ailab/blob/main/Real-CUGAN/upcunet_v3.py
"""
import torch
from torch import nn
from torch.nn import functional as F


# ---------------------------------------------------------------- Real-ESRGAN

class SRVGGNetCompact(nn.Module):
  def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
    super().__init__()
    self.upscale = upscale
    self.body = nn.ModuleList()
    self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
    self.body.append(nn.PReLU(num_parameters=num_feat))
    for _ in range(num_conv):
      self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
      self.body.append(nn.PReLU(num_parameters=num_feat))
    self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
    self.upsampler = nn.PixelShuffle(upscale)

  def forward(self, x):
    out = x
    for layer in self.body:
      out = layer(out)
    out = self.upsampler(out)
    return out + F.interpolate(x, scale_factor=self.upscale, mode='nearest')


class ResidualDenseBlock(nn.Module):
  def __init__(self, num_feat=64, num_grow_ch=32):
    super().__init__()
    self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
    self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
    self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
    self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
    self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)

  def forward(self, x):
    lrelu = lambda t: F.leaky_relu(t, 0.2)
    x1 = lrelu(self.conv1(x))
    x2 = lrelu(self.conv2(torch.cat((x, x1), 1)))
    x3 = lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
    x4 = lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
    x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
    return x5 * 0.2 + x


class RRDB(nn.Module):
  def __init__(self, num_feat, num_grow_ch=32):
    super().__init__()
    self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
    self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
    self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)

  def forward(self, x):
    return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x


class RRDBNet(nn.Module):
  def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32):
    super().__init__()
    self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
    self.body = nn.Sequential(*[RRDB(num_feat, num_grow_ch) for _ in range(num_block)])
    self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
    self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
    self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
    self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
    self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)

  def forward(self, x):
    lrelu = lambda t: F.leaky_relu(t, 0.2)
    feat = self.conv_first(x)
    feat = feat + self.conv_body(self.body(feat))
    feat = lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode='nearest')))
    feat = lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode='nearest')))
    return self.conv_last(lrelu(self.conv_hr(feat)))


# ---------------------------------------------------------------- Real-CUGAN

class SEBlock(nn.Module):
  def __init__(self, in_channels, reduction=8, bias=False):
    super().__init__()
    self.conv1 = nn.Conv2d(in_channels, in_channels // reduction, 1, 1, 0, bias=bias)
    self.conv2 = nn.Conv2d(in_channels // reduction, in_channels, 1, 1, 0, bias=bias)

  def forward(self, x):
    x0 = torch.mean(x, dim=(2, 3), keepdim=True)
    x0 = torch.sigmoid(self.conv2(F.relu(self.conv1(x0))))
    return x * x0


class UNetConv(nn.Module):
  def __init__(self, in_channels, mid_channels, out_channels, se):
    super().__init__()
    self.conv = nn.Sequential(
      nn.Conv2d(in_channels, mid_channels, 3, 1, 0),
      nn.LeakyReLU(0.1),
      nn.Conv2d(mid_channels, out_channels, 3, 1, 0),
      nn.LeakyReLU(0.1),
    )
    self.seblock = SEBlock(out_channels, reduction=8, bias=True) if se else None

  def forward(self, x):
    z = self.conv(x)
    return self.seblock(z) if self.seblock is not None else z


class UNet1(nn.Module):
  def __init__(self, in_channels, out_channels, deconv):
    super().__init__()
    self.conv1 = UNetConv(in_channels, 32, 64, se=False)
    self.conv1_down = nn.Conv2d(64, 64, 2, 2, 0)
    self.conv2 = UNetConv(64, 128, 64, se=True)
    self.conv2_up = nn.ConvTranspose2d(64, 64, 2, 2, 0)
    self.conv3 = nn.Conv2d(64, 64, 3, 1, 0)
    if deconv:
      self.conv_bottom = nn.ConvTranspose2d(64, out_channels, 4, 2, 3)
    else:
      self.conv_bottom = nn.Conv2d(64, out_channels, 3, 1, 0)

  def forward(self, x):
    x1 = self.conv1(x)
    x2 = self.conv1_down(x1)
    x1 = x1[:, :, 4:-4, 4:-4]
    x2 = self.conv2(F.leaky_relu(x2, 0.1))
    x2 = F.leaky_relu(self.conv2_up(x2), 0.1)
    x3 = F.leaky_relu(self.conv3(x1 + x2), 0.1)
    return self.conv_bottom(x3)


class UNet2(nn.Module):
  def __init__(self, in_channels, out_channels, deconv):
    super().__init__()
    self.conv1 = UNetConv(in_channels, 32, 64, se=False)
    self.conv1_down = nn.Conv2d(64, 64, 2, 2, 0)
    self.conv2 = UNetConv(64, 64, 128, se=True)
    self.conv2_down = nn.Conv2d(128, 128, 2, 2, 0)
    self.conv3 = UNetConv(128, 256, 128, se=True)
    self.conv3_up = nn.ConvTranspose2d(128, 128, 2, 2, 0)
    self.conv4 = UNetConv(128, 64, 64, se=True)
    self.conv4_up = nn.ConvTranspose2d(64, 64, 2, 2, 0)
    self.conv5 = nn.Conv2d(64, 64, 3, 1, 0)
    if deconv:
      self.conv_bottom = nn.ConvTranspose2d(64, out_channels, 4, 2, 3)
    else:
      self.conv_bottom = nn.Conv2d(64, out_channels, 3, 1, 0)

  def forward(self, x):
    x1 = self.conv1(x)
    x2 = self.conv1_down(x1)
    x1 = x1[:, :, 16:-16, 16:-16]
    x2 = self.conv2(F.leaky_relu(x2, 0.1))
    x3 = self.conv2_down(x2)
    x2 = x2[:, :, 4:-4, 4:-4]
    x3 = self.conv3(F.leaky_relu(x3, 0.1))
    x3 = F.leaky_relu(self.conv3_up(x3), 0.1)
    x4 = self.conv4(x2 + x3)
    x4 = F.leaky_relu(self.conv4_up(x4), 0.1)
    x5 = F.leaky_relu(self.conv5(x1 + x4), 0.1)
    return self.conv_bottom(x5)


class UpCunet2x(nn.Module):
  """input: (N, 3, H, W) in [0, 1], H / W even. output: (N, 3, 2H, 2W), not clamped."""
  def __init__(self, in_channels=3, out_channels=3):
    super().__init__()
    self.unet1 = UNet1(in_channels, out_channels, deconv=True)
    self.unet2 = UNet2(in_channels, out_channels, deconv=False)

  def forward(self, x):
    x = F.pad(x, (18, 18, 18, 18), 'reflect')
    x = self.unet1(x)
    x0 = self.unet2(x)
    return x0 + x[:, :, 20:-20, 20:-20]


class UpCunet4x(nn.Module):
  """input: (N, 3, H, W) in [0, 1], H / W even. output: (N, 3, 4H, 4W), not clamped."""
  def __init__(self, in_channels=3, out_channels=3):
    super().__init__()
    self.unet1 = UNet1(in_channels, 64, deconv=True)
    self.unet2 = UNet2(64, 64, deconv=False)
    self.ps = nn.PixelShuffle(2)
    self.conv_final = nn.Conv2d(64, 12, 3, 1, padding=0, bias=True)

  def forward(self, x):
    x00 = x
    x = F.pad(x, (19, 19, 19, 19), 'reflect')
    x = self.unet1(x)
    x0 = self.unet2(x)
    x = self.conv_final(x0 + x[:, :, 20:-20, 20:-20])
    x = self.ps(x[:, :, 1:-1, 1:-1])
    return x + F.interpolate(x00, scale_factor=4, mode='nearest')
