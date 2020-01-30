meh
---
Python image viewer for Windows based (loosely) on feh.

Dependencies
------------
Python 3.5+
Pillow
pywin32
send2trash

Recommended Usage
-----------------
The meh.bat script simplifies use for Windows users.
User may set this script as default application for image files.
Or drag-and-drop a file or folder onto the script.
Or add a shortcut to this script to their SendTo folder.
Update the script to include desired options.

Other Usage
-----------
Script can be called from the command line or imported as a library using Python.
This is not recommened (on Linux, recommend writing a .sh script) after removing Windows packages.

Controls
--------
space             : pause
enter             : go to next image in sequence
right             : go to next image in sequence
left              : go to previous image in sequence
down              : go to last viewed image
page up           : go to last image of previous folder
page down         : go to first image of next folder
z                 : go to random image
q                 : shuffle/sort sequence
y                 : reload image list from paths
F11               : toggle fullscreen
escape            : exit
delete            : delete image from computer (send to Recycle Bin)
ctrl+shift+delete : delete folder from computer (send to Recycle Bin)

License
-------
"THE BEER-WARE LICENSE" (Revision 42):
<gercunderscore4@gmail.com> wrote this file. As long as you retain this 
notice you can do whatever you want with this stuff. If we meet some day, 
and you think this stuff is worth it, you can buy me a beer in return.
Geoffrey Card
