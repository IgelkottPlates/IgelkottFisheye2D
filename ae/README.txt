IgelkottFisheye for Adobe After Effects
=======================================

IgelkottFisheye is an After Effects effect (32 bits per channel, SmartFX). It plays
the square fisheye clip (PYXIS 12K, Sony Venice 2 or Z-Cam E2 S6, lens pointing up
or down, any size) straight onto a wall, the way IgelkottStage does: one
resampling, through the lens model. It is the same effect as the IgelkottFisheye
node for Assimilate Live FX and the Fuse for DaVinci Resolve.

Tested in After Effects 27.0 on a Mac and 26.5 on Windows: a real ProRes 4444
plate rendered by After Effects, compared pixel for pixel with the lens model.


Install
-------
Quit After Effects, then copy the plugin to Adobe's common plug-in folder:

  Mac:      IgelkottFisheye.plugin  ->  /Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/
  Windows:  IgelkottFisheye.aex     ->  C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\

On a Mac, in Terminal, from the unpacked folder:
  sudo cp -R AfterEffects/IgelkottFisheye.plugin "/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
  sudo xattr -dr com.apple.quarantine "/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/IgelkottFisheye.plugin"

Start After Effects. The effect is under Effect > Igelkott > IgelkottFisheye.


Setting up a wall
-----------------
1. Make a composition the size of the wall, for example 3840 x 2160.
2. Put the fisheye clip in it, centred (the default for a new layer).
3. Apply Effect > Igelkott > IgelkottFisheye to the clip.
4. Set Wall Width and Wall Height to the composition's size.

The effect reads the whole plate at its own size and writes a Wall Width x
Wall Height picture centred on the layer, so the wall fills the composition.


Using the effect
----------------
Camera and Pointing on Auto (tag), the default: the camera and whether the
lens pointed up (zenith) or down (nadir) are read from the small black and
white tag that IgelkottDarkroom and Fisheye to Equi write next to the QR codes
in the corners. Choose a camera, and Zenith or Nadir, to set them by hand. A
plate without the tag is not an Igelkott clip and is not played: the output is
black with NOT AN IGELKOTT CLIP / IGELKOTTPLATES.COM and a small yellow warning
sign in the top left corner.

Yaw, Pitch and Roll aim the wall. FOV is the horizontal angle, from the wall's
left edge to its right edge. Offset X / Y move the finished picture, in output
pixels (+X right, +Y up).

Mode: Wall (a flat view) or Equirect: 360 degrees over the whole width, with
the same degrees per pixel up and down, aimed with Yaw, Pitch and Roll.

Split puts two walls side by side from the same plate, with a sharp edge at
Split Position; the right wall has its own Right Yaw / Pitch / Roll / FOV and
Right Offset X / Y.

The effect does not change colour: interpret the clip as for any other plate
(Igelkott plates are ACEScg / ACEScct).

It runs on the processor, on all cores: about 64 ms for a 3840 x 2160 frame on
an M3 Ultra Mac. At Full resolution After Effects' own ProRes decoding of
the large plate takes longer than the effect.


Files
-----
  IgelkottFisheye.plugin  the effect (Mac, Apple Silicon and Intel)
  IgelkottFisheye.aex     the effect (Windows)
  README.txt              this file

Igelkott Film AB, https://igelkottplates.com
