#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
'''
FILE: meh.py

PURPOSE: I wanted something like feh on Windows, so I built this.

NOTES:
    - Requires python 2.7, PIL, ImageTk
      on raspberry-pi (untested, I already installed these):
        sudo apt-get install python-pip
        sudo apt-get install python-tk
        sudo apt-get install libjpeg-dev libfreetype6 libfreetype6-dev zlib1g-dev
        sudo apt-get install python-imaging
        or try https://www.pkimber.net/howto/python/modules/pillow.html
        sudo apt-get install python-imaging
    - controls:
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
          delete            : permanently delete image from computer (skip Recycle Bin)
          ctrl+shift+delete : permanently delete folder from computer (skip Recycle Bin)

HISTORY:
    (see git)

TODO:
    - simplify code
'''

import os
import re
import time
import pdb
try:
    import Tkinter as tk # python2
except:
    import tkinter as tk # python3
from PIL import Image, ImageTk
from argparse import ArgumentParser
from random import randint, shuffle
import pdb
import shutil

defaultwidth  = 800
defaultheight = 600
defaultx      = 0
defaulty      = 0

class SlideShow:
    def __init__(self, pathlist=[], recurse=False, regex='.', fullscreen=True, delay=1.0, zoomed=True, width=defaultwidth, height=defaultheight, x=defaultx, y=defaulty, shuffle=False):
        # window
        self.title       = 'meh.py'
        self.fullscreen  = fullscreen
        self.width       = width
        self.height      = height
        self.x           = x
        self.y           = y
        # slide show
        self.zoomed      = zoomed
        self.paused      = False
        self.delayms     = int(delay*1000)
        self.slide       = None
        self.shuffle     = shuffle
        self.reloadId    = None
        # image selection
        self.recurse     = recurse
        self.pattern     = re.compile(regex) # filter files
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
        # misc
        self.listdeleted = True
        
        if self.imagepaths:
            # init Tkinter window
            self.root = tk.Tk()
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
            self.root.bind("<F11>", self.toggle_fullscreen)
            self.root.bind("<z>", self.rand_index)
            self.root.bind("<q>", self.shuffle_sort)
            self.root.bind("<y>", self.reload_imagepaths)
            self.root.bind("<Left>", self.prev_index)
            self.root.bind("<Right>", self.next_index)
            self.root.bind("<Down>", self.go_back)
            self.root.bind("<Prior>", self.prev_dir) # page up
            self.root.bind("<Control-Left>", self.prev_dir)
            self.root.bind("<Next>", self.next_dir) # page down
            self.root.bind("<Control-Right>", self.next_dir)
            self.root.bind("<space>", self.pause_play)
            self.root.bind("<Return>", self.next_index)
            self.root.bind("<Escape>", self.close_out)
            self.root.bind("<Control-Shift-Delete>", self.delete_folder)
            self.root.bind("<Delete>", self.delete_file)
            self.root.bind("<Configure>", self.on_resize) # not working

            # show
            self.showloop()
            self.root.mainloop()

            # quit
            try:
                self.root.destroy()
            except:
                pass
        else:
            print('No images found')
    
    
    def get_image_paths(self, pathlist):
        for path in pathlist:
            path = os.path.abspath(path)
            if os.path.isfile(path):
                # single file
                yield(path)
            elif os.path.isdir(path):
                # directory
                if self.recurse:
                    # and all subdirectories
                    for root, dirs, filenames in os.walk(path):
                        for filename in filenames:
                            yield(os.path.join(root,filename))
                else:
                    for item in os.listdir(path):
                        item = os.path.join(path,item)
                        if os.path.isfile(item):
                            yield(item)
    
    
    def filter_imagepaths(self, path):
        return (path.split('.')[-1] in ('png', 'jpg', 'jpeg', 'gif')) and self.pattern.search(path)
    
    
    def update_imagepaths(self):
        self.imagepaths = sorted(list(filter(self.filter_imagepaths, self.get_image_paths(self.pathlist))))
        self.length     = len(self.imagepaths)
        self.index      = len(self.imagepaths)-1
        self.previous   = 0
        return self.imagepaths
    
    
    def selectImage(self, force=False):
        # get image
        print('{}/{}  rand:{}  {}'.format(self.index, len(self.imagepaths), self.shuffle, self.imagepaths[self.index]))
        if self.title != self.imagepaths[self.index] or force:
            self.title = self.imagepaths[self.index]
            self.root.wm_title(self.title)
            self.img = Image.open(self.title)
            if self.title.lower().endswith('.gif'):
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
    
    
    def next_dir(self, event=None):
        index_dir = os.path.dirname(self.imagepaths[self.index])
        for i in range(self.length):
            temp = (self.index + i) % self.length
            if index_dir != os.path.dirname(self.imagepaths[temp]):
                break
        else:
            temp = (self.index + 1) % self.length
        self.previous = self.index
        self.index = temp
        self.show_and_reset_timer()
        return "break"
    
    
    def prev_dir(self, event=None):
        index_dir = os.path.dirname(self.imagepaths[self.index])
        for i in range(self.length):
            temp = (self.index - i) % self.length
            if index_dir != os.path.dirname(self.imagepaths[temp]):
                break
        else:
            temp = (self.index - 1) % self.length
        self.previous = self.index
        self.index = temp
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
        self.length -= 1
        self.imagepaths = self.imagepaths[:self.index] + self.imagepaths[self.index+1:]
        # delete
        print('Delete file: ' + path)
        if self.listdeleted:
            with open("deleted.txt", "a") as fout:
                filename = os.path.basename(path)
                fout.write(filename.lower() + '\n')
        os.remove(path)
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
        path = self.imagepaths[self.index]
        index = self.index
        dir = os.path.dirname(path)
        print('Delete folder: ' + dir)
        if self.listdeleted:
            with open("deleted.txt", "a") as fout:
                fout.write(os.path.basename(dir).lower() + '\n')
                for root, dirs, filenames in os.walk(dir):
                    for filename in filenames:
                        subpath = os.path.join(root,filename)
                        fout.write(filename.lower() + '\n')
        shutil.rmtree(dir)
        self.update_imagepaths()
        # change image (close if none left)
        if self.length > 0:
            self.index = index % self.length
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
                        help='recurse though path directory',
                        default=False)
    parser.add_argument('-R', '--random',
                        action='store_true',
                        help='random order',
                        default=False)
    parser.add_argument('-f', '--fullscreen',
                        action='store_true',
                        help='make canvas size of screen',
                        default=False)
    parser.add_argument('-z', '--zoomed',
                        action='store_true',
                        help='scale images until they fit the screensize (without altering relative dimensions)',
                        default=False)
    parser.add_argument('-d', '--delay',
                        action='store',
                        type=float,
                        help='delay (in seconds) before new slide is shown',
                        default=10)
    parser.add_argument('-g', '--geometry',
                        action='store',
                        type=str,
                        help='geometry in the form wxh[+x+y]',
                        default='{}x{}+{}+{}'.format(defaultwidth,defaultheight,defaultx,defaulty))
    # python meh.py "/personal/photos/Japan" -d 15 -z -r -R -g "910x930+0+0" &
    # python meh.py "/personal/photos/Japan" -d 15 -z -r -R -g "910x930+910+0" &
    args = parser.parse_args()
    
    mat = re.match(r'\s*(?P<width>\d+)x(?P<height>\d+)\+(?P<x>\d+)\+(?P<y>\d+)\s*',args.geometry)
    if mat:
        width  = int(mat.groupdict()['width'])
        height = int(mat.groupdict()['height'])
        x      = int(mat.groupdict()['x'])
        y      = int(mat.groupdict()['y'])
        print('geometry {}x{}+{}+{}'.format(width,height,x,y))
    else:
        width  = defaultwidth
        height = defaultheight
        x      = defaultx
        y      = defaulty
        print('default geometry')
    
    sldshw = SlideShow(pathlist   = args.paths,
                       recurse    = args.recurse,
                       regex      = args.regex,
                       fullscreen = args.fullscreen,
                       zoomed     = args.zoomed,
                       delay      = args.delay,
                       width      = width,
                       height     = height,
                       x          = x,
                       y          = y,
                       shuffle    = args.random)
