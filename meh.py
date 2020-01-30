#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
I wanted something like feh (image viewer) on Windows, so I built this.

usage: meh.py [-h] [--regex [REGEX]] [-r] [-R] [-f] [-z] [-a] [-d DELAY]
              [-g GEOMETRY]
              [paths [paths ...]]

positional arguments:
  paths                 path(s) to image(s) or folder(s) of image(s)

optional arguments:
  -h, --help            show this help message and exit
  --regex [REGEX]       regex filter on file paths
  -r, --recurse         recurse though path directory
  -R, --random          shuffle order
  -f, --fullscreen      set to fullscreen mode
  -z, --zoomed          scale images to fit the window (without distorting or
                        obscuring them)
  -a, --auto            autoplay (advance after 'delay' seconds)
  -d DELAY, --delay DELAY
                        delay (in seconds) before new slide is shown
  -g GEOMETRY, --geometry GEOMETRY
                        window geometry in the form wxh+x+y (from top-left)

Controls:
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

Todo:
    - simplify code
    - consider using log
    - add SVG?
    - thread next image loading

For SVG:
    # https://stackoverflow.com/questions/15130670/pil-and-vectorbased-graphics
    from io import BytesIO
    import cairosvg
    out = BytesIO()
    cairosvg.svg2png(url='path/to/svg', write_to=out)
    image = Image.open(out)
'''

import re, pdb
from pathlib import Path
from argparse import ArgumentParser
from random import randint, shuffle
import tkinter as tk
# installed
from PIL import Image, ImageTk
import win32gui, win32con
from send2trash import send2trash


class SlideShow:
    FILE_TYPES_LC = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

    def __init__(self, pathlist, recurse, regex, fullscreen, paused, delay, zoomed, width, height, x, y, shuffle):
        # window
        self.title       = 'meh.py'
        self.fullscreen  = fullscreen
        self.width       = width
        self.height      = height
        self.x           = x
        self.y           = y
        # slide show
        self.zoomed      = zoomed
        self.paused      = paused
        self.delayms     = int(delay*1000)
        self.slide       = None
        self.shuffle     = shuffle
        self.reloadId    = None
        # image selection
        self.recurse     = recurse
        self.pattern     = re.compile(regex, re.IGNORECASE) # filter files
        self.pathlist    = pathlist # list of images or directories to search
        self.update_imagepaths()
        #self.imagepaths = self.update_imagepaths() # automatically loads variables
        #self.length     = len(self.imagepaths)
        #self.index      = len(self.imagepaths)-1
        #self.previous   = 0
        self.img         = None
        # animation
        self.gif         = False
        self.gifCounter  = 0
        self.i           = 0

        if self.imagepaths:
            # init Tkinter window
            self.root = tk.Tk()
            self.root.iconbitmap(Path(__file__).parent / 'icon' / 'meh.ico')
            if self.fullscreen:
                self.width      = self.root.winfo_screenwidth()
                self.height     = self.root.winfo_screenheight()
                self.root.geometry('{}x{}'.format(self.width,self.height))
            else:
                # set the dimensions of the screen
                # and where it is placed
                self.root.geometry('%dx%d+%d+%d' % (self.width, self.height, self.x, self.y))
            self.frame = tk.Frame(self.root, bg='black', width=self.width, height=self.height, bd=0)
            self.frame.pack(fill=tk.BOTH, expand=1)
            self.canvas = tk.Canvas(self.frame, bg='black', width=self.width, height=self.height, bd=0, highlightthickness=0, relief='ridge')
            self.canvas.pack(fill=tk.BOTH, expand=1)

            self.root.attributes("-fullscreen", self.fullscreen)

            # controls
            self.root.bind("<F11>",                  self.toggle_fullscreen)
            self.root.bind("<z>",                    self.rand_index)
            self.root.bind("<q>",                    self.shuffle_sort)
            self.root.bind("<y>",                    self.reload_imagepaths)
            self.root.bind("<Left>",                 self.prev_index)
            self.root.bind("<Right>",                self.next_index)
            self.root.bind("<Down>",                 self.go_back)
            self.root.bind("<Prior>",                self.prev_dir) # page up
            self.root.bind("<Control-Left>",         self.prev_dir)
            self.root.bind("<Next>",                 self.next_dir) # page down
            self.root.bind("<Control-Right>",        self.next_dir)
            self.root.bind("<space>",                self.pause_play)
            self.root.bind("<Return>",               self.next_index)
            self.root.bind("<Escape>",               self.close_out)
            self.root.bind("<Control-Shift-Delete>", self.delete_folder)
            self.root.bind("<Delete>",               self.delete_file)
            self.root.bind("<Configure>",            self.on_resize) # not working

            # show
            self.show() # in case paused
            self.showloop()
            self.root.mainloop()

            # quit
            try:
                self.root.destroy()
            except:
                pass
        else:
            print('No images found')




    def update_imagepaths(self):
        '''
        From given paths, get all files in the current directory.
        Recurse if requested.
        Can be called again to update.
        '''

        # setup glob string
        globStr = '*.*'
        if self.recurse:
            globStr = '**/' + globStr

        # generate list of all paths
        self.imagepaths = []
        firstPath = None
        for path in self.pathlist:
            # convert to path
            path = Path(path).resolve()
            # if a file, get directory
            # (users typically like to be able to scroll through the current directory)
            # except we need to start with that file
            if path.is_file():
                # grab first file path, use later to decide which image goes first
                if firstPath is None:
                    firstPath = path
                # get folder
                path = path.parent
            # get all files in directory
            if path.is_dir():
                for f in path.glob(globStr):
                    if f.is_file() and \
                       (f.suffix.lower() in SlideShow.FILE_TYPES_LC) and \
                       (self.pattern.search(str(f)) is not None):
                        self.imagepaths.append(f.resolve())

        # sort list
        self.imagepaths.sort()

        # get length
        self.length = len(self.imagepaths)

        # choose a starting index
        self.index = 0
        if firstPath is not None:
            for i,f in enumerate(self.imagepaths):
                if f.samefile(firstPath):
                    self.index = i
                    break
        # set previous
        self.previous = self.index

        return self.imagepaths


    def selectImage(self, force=False):
        # get image
        print('{:{w:}}/{:{w:}}  rand:{:<5}  "{}"'.format(self.index, self.length, str(self.shuffle), self.imagepaths[self.index], w=len(str(self.length))))
        if self.title != self.imagepaths[self.index] or force:
            self.title = self.imagepaths[self.index]
            self.root.wm_title(self.title)
            self.img = Image.open(self.title)
            if self.title.suffix.lower() == '.gif':
                # get delay
                try:
                    self.gifDelay = self.img.info['duration']
                except:
                    self.gifDelay = 100
                # get frames
                self.gif = []
                try:
                    while 1:
                        self.gif.append(self.img.copy())
                        self.img.seek(self.img.tell()+1)
                except EOFError:
                    pass
                # initialize
                self.i = 0
                self.img = self.gif[self.i]
                self.gifId = self.root.after(self.gifDelay, self.gifLoop)
            else:
                self.gif = None


    def gifLoop(self, event=None):
        if self.gif:
            self.i = (self.i + 1) % len(self.gif)
            self.img = self.gif[self.i]
            # draw frame
            self.showSlide()
            if self.gifId:
                self.root.after_cancel(self.gifId)
            self.gifId = self.root.after(self.gifDelay, self.gifLoop)


    def resizeImage(self):
        if self.zoomed:
            if self.gif:
                widthratio = float(self.width)/self.img.size[0]
                heightratio = float(self.height)/self.img.size[1]
                if widthratio < heightratio:
                    for i in range(len(self.gif)):
                        self.gif[i] = self.gif[i].resize((int(self.width), int(self.img.size[1]*widthratio)), Image.ANTIALIAS)
                else:
                    for i in range(len(self.gif)):
                        self.gif[i] = self.gif[i].resize((int(self.img.size[0]*heightratio), int(self.height)), Image.ANTIALIAS)
            else:
                widthratio = float(self.width)/self.img.size[0]
                heightratio = float(self.height)/self.img.size[1]
                if widthratio < heightratio:
                    self.img = self.img.resize((int(self.width), int(self.img.size[1]*widthratio)), Image.ANTIALIAS)
                else:
                    self.img = self.img.resize((int(self.img.size[0]*heightratio), int(self.height)), Image.ANTIALIAS)


    def reload(self, event=None):
        self.selectImage(force=True)
        self.resizeImage()
        self.showSlide()


    def show(self):
        self.selectImage()
        self.resizeImage()
        self.showSlide()


    def showSlide(self):
        # display slide
        self.photoimage = ImageTk.PhotoImage(self.img)
        self.canvas.pack()

        # switch slides
        if self.slide:
            self.canvas.delete(self.slide)
        self.slide = self.canvas.create_image(self.width/2, self.height/2, image=self.photoimage)


    def showloop(self):
        # increment index
        if not self.paused:
            if self.shuffle:
                # random
                self.get_rand()
            else:
                # next
                self.get_next()
            self.show()
        # requeue in loop
        self.looperid = self.root.after(self.delayms, self.showloop)


    def get_rand(self):
        self.previous = self.index
        # this math avoids repeating the current image
        newindex = randint(0,self.length-2)
        newindex += 1 if newindex >= self.index else 0
        self.index = newindex


    def get_prev(self):
        self.previous = self.index
        self.index = (self.index - 1) % self.length


    def get_next(self):
        self.previous = self.index
        self.index = (self.index + 1) % self.length


    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        #pdb.set_trace()
        self.root.attributes("-fullscreen", self.fullscreen)
        if self.fullscreen:
            self.width = self.root.winfo_screenwidth()
            self.height = self.root.winfo_screenheight()
        else:
            self.width = defaultwidth
            self.height = defaultheight
        # resize and re-show image, if zoomed
        self.root.geometry('{}x{}'.format(self.width,self.height))
        self.show()
        return "break"


    def show_and_reset_timer(self):
        if self.looperid:
            self.root.after_cancel(self.looperid)
        self.show()
        self.looperid = self.root.after(self.delayms, self.showloop)


    def next_index(self, event=None):
        if self.shuffle:
            self.get_rand()
        else:
            self.get_next()
        self.show_and_reset_timer()
        return "break"


    def prev_index(self, event=None):
        self.get_prev()
        self.show_and_reset_timer()
        return "break"


    def first_of_next_dir(self):
        current_dir = self.imagepaths[self.index].parent
        # move until folder does not match
        temp = self.index
        for i in range(self.length):
            temp = (temp + 1) % self.length
            if not current_dir.samefile(self.imagepaths[temp].parent):
                break
        else:
            # failed to find a different folder, just get next
            temp = (self.index + 1) % self.length
        return temp


    def last_of_prev_dir(self):
        current_dir = self.imagepaths[self.index].parent
        # move until folder does not match
        temp = self.index
        for i in range(self.length):
            temp = (temp - 1) % self.length
            if not current_dir.samefile(self.imagepaths[temp].parent):
                break
        else:
            # failed to find a different folder, just get next
            temp = (self.index + 1) % self.length
        return temp


    def next_dir(self, event=None):
        self.previous = self.index
        self.index = self.first_of_next_dir()
        self.show_and_reset_timer()
        return "break"


    def prev_dir(self, event=None):
        self.previous = self.index
        self.index = self.last_of_prev_dir()
        self.show_and_reset_timer()
        return "break"


    def rand_index(self, event=None):
        self.get_rand()
        self.show_and_reset_timer()
        return "break"


    def go_back(self, event=None):
        temp = self.index
        self.index = self.previous
        self.previous = temp
        self.show_and_reset_timer()
        return "break"


    def pause_play(self, event=None):
        self.paused = not self.paused
        return "break"


    def shuffle_sort(self, event=None):
        self.shuffle = not self.shuffle
        return "break"


    def delete_file(self, event=None):
        path = self.imagepaths[self.index]
        # remove it from slideshow
        self.imagepaths = self.imagepaths[:self.index] + self.imagepaths[self.index+1:]
        self.length -= 1
        # delete
        print('Delete file: "{}"'.format(path))
        send2trash(str(path))
        # change image (close if none left)
        if self.length > 0:
            self.index %= self.length
            self.show_and_reset_timer()
        else:
            try:
                self.root.destroy()
            except:
                pass
            return "break"


    def delete_folder(self, event=None):
        # save current-index and previous-index-not-in-this-folder
        index = self.index
        prev_dir_index = self.last_of_prev_dir()
        # delete folder
        dir = self.imagepaths[self.index].parent
        print('Delete folder: "{}"'.format(dir))
        for item in dir.rglob('*'):
            print('Delete file: "{}"'.format(item))
        send2trash(str(dir))
        # easier to simply update full list
        self.update_imagepaths()
        # change image (close if none left)
        if self.length > 0:
            self.index = (prev_dir_index + 1) % self.length
            self.back = index % self.length # last position, even if it doesn't exist
            self.show_and_reset_timer()
        else:
            try:
                self.root.destroy()
            except:
                pass
            return "break"


    def close_out(self, event=None):
        try:
            self.root.destroy()
        except:
            pass
        return "break"


    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        if self.width != event.width or self.height != event.height:
            self.width = event.width
            self.height = event.height
            # slows things down, but updates resolution
            #self.img = Image.open(self.title)
            #self.resizeImage()
            #self.showSlide()
            # reload image after a moment
            if self.reloadId:
                self.root.after_cancel(self.reloadId)
            self.reloadId = self.root.after(200, self.reload)


    def reload_imagepaths(self, event=None):
        self.update_imagepaths()
        return "break"


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('paths',
                        nargs='*',
                        help='path(s) to image(s) or folder(s) of image(s)',
                        default=['.'])
    parser.add_argument('--regex',
                        nargs='?',
                        help='regex filter on file paths',
                        default=r'.')
    parser.add_argument('-r', '--recurse',
                        action='store_true',
                        help='recurse though path directory')
    parser.add_argument('-R', '--random',
                        action='store_true',
                        help='shuffle order')
    parser.add_argument('-f', '--fullscreen',
                        action='store_true',
                        help='set to fullscreen mode')
    parser.add_argument('-z', '--zoomed',
                        action='store_true',
                        help='scale images to fit the window (without distorting or obscuring them)')
    parser.add_argument('-a', '--auto',
                        action='store_true',
                        help='autoplay (advance after \'delay\' seconds)')
    parser.add_argument('-d', '--delay',
                        action='store',
                        type=float,
                        help='delay (in seconds) before new slide is shown',
                        default=10)
    parser.add_argument('-g', '--geometry',
                        action='store',
                        type=str,
                        help='window geometry in the form wxh+x+y (from top-left)',
                        default='')
    args = parser.parse_args()

    # hide console window
    # https://www.semicolonworld.com/question/43710/how-to-hide-console-window-in-python
    try:
        frgrnd_wndw = win32gui.GetForegroundWindow();
        wndw_title  = win32gui.GetWindowText(frgrnd_wndw);
        if wndw_title.endswith('python.exe') or wndw_title.endswith('py.exe'):
            win32gui.ShowWindow(frgrnd_wndw, win32con.SW_HIDE);
    except:
        pass

    # parse geometry
    mat = re.match(r'\s*(?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)\s*', args.geometry)
    if mat:
        width  = int(mat.groupdict()['width'])
        height = int(mat.groupdict()['height'])
        x      = int(mat.groupdict()['x'])
        y      = int(mat.groupdict()['y'])
        print('geometry {}x{}+{}+{}'.format(width,height,x,y))
    else:
        width  = 800
        height = 600
        x      = 0
        y      = 0

    sldshw = SlideShow(pathlist   = args.paths,
                       recurse    = args.recurse,
                       regex      = args.regex,
                       fullscreen = args.fullscreen,
                       zoomed     = args.zoomed,
                       paused     = not args.auto,
                       delay      = args.delay,
                       width      = width,
                       height     = height,
                       x          = x,
                       y          = y,
                       shuffle    = args.random)
