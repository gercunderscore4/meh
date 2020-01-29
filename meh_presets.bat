REM #!/bin/bash

REM Example script for easily dragging and dropping folders for viewing.
REM Auto-play with a 15s delay
REM Zoom image to fill screen without distortion
REM Recusively look through folders
REM Randomize order
REM Create 960 x 1080 window (960 = 1920 / 2)
REM At 0 x 0 in top left corner

REM Windows version of the command
start python "%~dp0\meh.py" %1 -d 15 -z -r -R -g "960x1080+0+0"

REM # Linux version of the command (untested)
REM python meh.py" "$1" -d 15 -z -r -R -g "910x930+0+0" &
