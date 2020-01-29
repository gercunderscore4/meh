REM Call PowerShell (needs to be called from a Batch file to avoid security block)
REM PowerShell window will be invisible
REM For debug, replace "-WindowStyle Hidden" with "-Exit"

REM PowerShell calls python launcher, with meh.py from this location, and the first input argument
REM First input is a path when using drag-and-drop (onto this script)
REM User may also set this script as default application for image files

REM usage: meh.py [-h] [--regex [REGEX]] [-r] [-R] [-f] [-z] [-a] [-d DELAY]
REM               [-g GEOMETRY]
REM               [paths [paths ...]]
REM 
REM positional arguments:
REM   paths                 path(s) to image(s) or folder(s) of image(s)
REM 
REM optional arguments:
REM   -h, --help            show this help message and exit
REM   --regex [REGEX]       regex filter on file paths
REM   -r, --recurse         recurse though path directory
REM   -R, --random          shuffle order
REM   -f, --fullscreen      set to fullscreen mode
REM   -z, --zoomed          scale images to fit the window (without distorting or
REM                         obscuring them)
REM   -a, --auto            autoplay (advance after 'delay' seconds)
REM   -d DELAY, --delay DELAY
REM                         delay (in seconds) before new slide is shown
REM   -g GEOMETRY, --geometry GEOMETRY
REM                         window geometry in the form wxh+x+y (from top-left)

PowerShell -WindowStyle Hidden -Command "py -3 '%~dp0meh.py' -z '%1'"
