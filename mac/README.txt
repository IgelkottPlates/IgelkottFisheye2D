IgelkottFisheye for Assimilate Live FX (Mac)
============================================

IgelkottFisheye is a Matchbox node for Live FX. It plays the square fisheye
clip (PYXIS 12K or Sony Venice 2 + Entaniya HAL 250, lens pointing up or down,
any size) straight onto an LED wall, the way IgelkottStage does. Use it
instead of Eq->2D Transformer on each wall: same Yaw, Pitch, Roll and FOV, but
only one resampling, through the lens model the equirects are made with.

It needs nothing but Live FX itself. No app to open, nothing to sign.


Install
-------
1. Unpack the zip.
2. Quit Live FX if it is running.
3. In Finder, choose Go > Go to Folder... and paste
     /Library/Application Support/Assimilator/Plugins/Matchbox/shaders
   (the Library at the top of the disk, not the one in your home folder).
4. Copy IgelkottFisheye2D.glsl and IgelkottFisheye2D.xml into that folder.
   Replace the old files if Finder asks. It may ask for your password.
5. Start Live FX.

The node is then under
  Plug-ins.. > Matchbox > shaders > IgelkottFisheye2D

Or in Terminal, from the unpacked folder:
  sudo cp IgelkottFisheye2D.glsl IgelkottFisheye2D.xml "/Library/Application Support/Assimilator/Plugins/Matchbox/shaders/"


Uninstall
---------
Delete the two files from the same folder and restart Live FX.


Using the node
--------------
Put it on the fisheye clip, one node per wall.

Camera and Pointing on Auto (tag), the default: the camera and whether the
lens pointed up (zenith) or down (nadir) are read from the small black and
white tag that IgelkottDarkroom and Fisheye to Equi write next to the QR codes
in the corners. Choose PYXIS 12K, Sony Venice 2 or Z-Cam E2 S6, and Zenith or
Nadir, to set them by hand. A plate without the tag is not an Igelkott clip and
is not played: the output is black with NOT AN IGELKOTT CLIP / IGELKOTTPLATES.COM
and a small yellow warning sign in the top left corner.

Offset X / Y move the finished picture, after the projection, in output pixels
(+X right, +Y up). With Split on, they move the left wall's picture and Right
Offset X / Y the right wall's. The plate must be centred (as IgelkottDarkroom
and Fisheye to Equi make it).

Yaw, Pitch and Roll work as on Eq->2D Transformer. FOV is the horizontal
angle, from the wall's left edge to its right edge (with Split on, each wall's
own width): FOV 90 shows 90 degrees along the horizon.

Mode: Wall (a flat view) or Equirect: 360 degrees over the whole width, with
the same degrees per pixel up and down, aimed with Yaw, Pitch and Roll (the
whole sphere at 2:1, cropped top and bottom on wider canvases such as 32:9).

Split puts two walls side by side from the same plate, with a sharp edge at
Split Position; the right wall has its own Right Yaw / Pitch / Roll / FOV and
Right Offset X / Y. In Equirect each wall is a window at the same scale,
centred on its own Yaw / Pitch / Roll: Split 50 % with Right Yaw 180 shows the
whole 360 degrees side by side.

Use .mov clips. PNG image sequences are not supported: Live FX turns them
upside down.


Files
-----
  IgelkottFisheye2D.glsl / .xml     the node
  VERSION                           version of this package
  LICENSE.txt                       may be used only to play back Igelkott plates

Igelkott Film AB, https://igelkottplates.com
