IgelkottFisheye for PIXERA
==========================

IgelkottFisheye is a GLSL effect for PIXERA (AV Stumpfl). It plays the square
fisheye clip (PYXIS 12K or Sony Venice 2 + Entaniya HAL 250, lens pointing up
or down, any size) directly through the lens model. It is the same effect as
the IgelkottFisheye node for Assimilate Live FX.


Install
-------
1. In PIXERA, open the Effects library and select the Custom folder.
2. Drag "IgelkottFisheye.glsl" onto the Custom folder (or press + and choose
   the file). Keep the file name: PIXERA matches it to the effect's name.
3. The effect is then under Effects > Custom > IgelkottFisheye.


Using the effect
----------------
Camera and Pointing on Auto (tag), the default: the camera and whether the lens
pointed up (zenith) or down (nadir) are read from the small black and white tag
that IgelkottDarkroom and Fisheye to Equi write next to the QR codes in the
corners. Choose PYXIS 12K, Sony Venice 2 or Z-Cam E2 S6, and Zenith or Nadir,
to set them by hand. With Auto and no tag (PYXIS 12K / Zenith is used), a small
yellow warning sign shows in the top left corner.

Offset X / Y move the finished picture, after the projection, in % of the
layer's height (+X right, +Y up); with Split on, the left wall's picture, and
Right Offset X / Y the right wall's. The plate must be centred (as IgelkottDarkroom
and Fisheye to Equi make it).

Mode Wall is a flat view: Yaw, Pitch, Roll, a horizontal FOV from the wall's
left edge to its right edge (with Split on, each wall's own width), and the
layer's Aspect (width / height).

Mode Equirect gives 360 degrees over the layer's whole width, aimed with Yaw,
Pitch and Roll, with the same degrees per pixel up and down: the whole sphere
at Aspect 2, cropped top and bottom on wider layers (32:9: 101 degrees high),
black past the poles on narrower ones. Put PIXERA's own Equirectangular effect
after it for curved screens and domes, with Aspect 2 and Split off (with Split
on, the layer holds two windows, not one whole sphere).

Split: two walls side by side from the same plate, with a sharp edge at Split
Position (% of the width). The left wall uses Yaw / Pitch / Roll / FOV and
Offset, the right one Right Yaw / Pitch / Roll / FOV and Right Offset. In Mode
Equirect each wall is a window at the same scale, centred on its own Yaw /
Pitch / Roll.


Checked
-------
The effect is drawn on a graphics card (OpenGL 4.5 on Windows) and compared
pixel by pixel with the lens model: within 0.1 source pixels. In Mode
Equirect followed by PIXERA's own Equirectangular effect, every pixel lands
within 0.4 source pixels of where the lens model puts it.
Not yet checked inside PIXERA itself.


Igelkott Film AB
