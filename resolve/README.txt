IgelkottFisheye for DaVinci Resolve
===================================

IgelkottFisheye is a Fusion tool (a Fuse) for DaVinci Resolve and Fusion
Studio. It plays the square fisheye clip (PYXIS 12K, Sony Venice 2 or Z-Cam
E2 S6, lens pointing up or down, any size) straight onto a wall, the way
IgelkottStage does: one resampling, through the lens model, on the graphics
card. It is the same effect as the IgelkottFisheye node for Assimilate Live FX.

Tested in DaVinci Resolve Studio 21.1 on a Mac and 21.2 on Windows.


Install
-------
1. Quit Resolve.
2. Copy IgelkottFisheye.fuse to
     Mac:     ~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Fuses/
     Windows: C:\ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Fuses\
   (create the Fuses folder if it is not there).
3. Start Resolve.


Setting up a wall
-----------------
1. Set the timeline's resolution to the wall, for example 3840 x 2160.
2. Put the fisheye clip (.mov) on the timeline, select it and open the
   Fusion page. Use the clip's own Fusion page, not a Fusion Clip: a Fusion
   Clip shrinks the plate to the timeline before the effect.
3. Add Tool > Fuses > Igelkott > IgelkottFisheye, and put it between
   MediaIn1 and MediaOut1.
4. Set Wall Width and Wall Height to the timeline's resolution.

Back on the Edit page, the wall fills the timeline.


Using the tool
--------------
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

The tool does not change colour: set the clip's colour space in Resolve as for
any other plate (Igelkott plates are ACEScg / ACEScct).


Files
-----
  IgelkottFisheye.fuse    the tool
  README.txt              this file

Igelkott Film AB, https://igelkottplates.com
