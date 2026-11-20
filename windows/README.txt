IgelkottFisheye for Assimilate Live FX (Windows)
================================================

IgelkottFisheye is a Matchbox node for Live FX. It plays the square fisheye
clip (PYXIS 12K or Sony Venice 2 + Entaniya HAL 250, lens pointing up or down,
any size) straight onto an LED wall, the way IgelkottStage does. Use it
instead of Eq->2D Transformer on each wall: same Yaw, Pitch, Roll and FOV, but
only one resampling, through the lens model the equirects are made with.

Works with any graphics card that runs Live FX (NVIDIA or AMD). It needs
nothing but Live FX itself.


Install
-------
1. Unpack the whole zip to any folder.
2. Double-click "Install IgelkottFisheye.cmd".
   If Windows asks for administrator rights, say yes.
3. Restart Live FX (quit it first if it is running).

The node is then under
  Plug-ins.. > Matchbox > shaders > IgelkottFisheye2D

The installer copies two files to
  C:\ProgramData\Assimilator\plugin64\Matchbox\shaders
Running it again updates them; it does nothing if they are already current.


Uninstall
---------
Double-click "Uninstall IgelkottFisheye.cmd" and restart Live FX.


Using the node
--------------
Put it on the fisheye clip, one node per wall.

Plate Auto (default): the camera and whether the lens pointed up (zenith) or
down (nadir) are read from the small black and white tag that IgelkottDarkroom
and Fisheye to Equi write next to the QR codes in the corners. With no tag, a
small yellow warning sign shows in the top left corner and the Manual choice
below is used: switch to Manual, or use a plate with the tag.

Plate Manual: Camera (PYXIS 12K, Sony Venice 2, Z-Cam E2 S6) and Pointing
(Zenith, Nadir). Z-Cam E2 S6 has no lens model yet: the picture stays black.

Lens Offset X / Y move the lens centre, in source pixels at 8040 whatever the
clip's size. 0 for centred plates.

Yaw, Pitch, Roll and FOV work as on Eq->2D Transformer. FOV is the vertical
angle over the node's height.

Mode: Wall (a flat view) or Equirect (the whole sphere, 2:1).

Split puts two walls side by side from the same plate, with a sharp edge at
Split Position; the right wall has its own Right Yaw / Pitch / Roll / FOV.

Use .mov clips. PNG image sequences are not supported: Live FX turns them
upside down.

Hover over a control in Live FX for what it does.


PIXERA
------
The folder PIXERA holds the same effect for PIXERA (AV Stumpfl):
IgelkottFisheye.glsl and its own README.txt with how to install it.


Files
-----
  Install IgelkottFisheye.cmd       installs the node
  Uninstall IgelkottFisheye.cmd     removes it
  Install-IgelkottFisheye.ps1       the installer itself (used by both .cmd)
  IgelkottFisheye2D.glsl / .xml     the node
  PIXERA\                           the same effect for PIXERA
  VERSION                           version of this package

Igelkott Studios AB
