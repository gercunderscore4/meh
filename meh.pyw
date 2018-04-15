"""
feh doesn't work on windows, so I need a good terminal accessible image viewing program
requires python 2.7, PIL, ImageTk

TODO: Make window resizable
      Find a way to avoid the issue where a Windows path with a space ends with \", e.g. "C:\Path\With Space\"
      Allow multiple paths
      More features
"""

import os
import Tkinter as tk
import PIL, ImageTk
from PIL import Image
from argparse import ArgumentParser
from random import randint, shuffle
import pdb

defaultwidth = 800
defaultheight = 600

def get_paths(path, recursive=True):
    pathlist = []
    if os.path.isfile(path):
        # single file
        pathlist.append(path)
    elif os.path.isdir(path):
        # directory
        if recursive:
            # and all subdirectories
            for root, dirs, files in os.walk(path):
                for filename in files:
                    pathlist.append(os.path.join(root,filename))
        else:
            for item in os.listdir(path):
                itempath = os.path.join(path,item)
                if os.path.isfile(itempath):
                    pathlist.append(itempath)
    return pathlist


def images_only(pathlist):
    newlist = []
    for path in pathlist:
        if os.path.isfile(path) and os.path.splitext(path)[-1] in ['.png', '.jpg', '.jpeg', '.gif']:
            newlist.append(path)
    return newlist


class SlideShow:
    def __init__(self, imagepaths=[], fullscreen=True, delay=1.0, zoomed=True, width=defaultwidth, height=defaultheight):
        self.imagepaths = imagepaths # list of absolute paths to images
        self.fullscreen = fullscreen
        self.delay      = delay
        self.zoomed     = zoomed
        self.paused     = False
        self.shuffled   = False
        self.width      = width
        self.height     = height
        self.slide      = None
        self.reel       = imagepaths
        self.index      = 0
        self.looperid   = None

        if imagepaths:
            # init Tkinter window
            self.root = tk.Tk()
            if self.fullscreen:
                self.width      = self.root.winfo_screenwidth()
                self.height     = self.root.winfo_screenheight()
            self.root.geometry('{}x{}'.format(self.width,self.height))
            self.frame = tk.Frame(self.root, bg='black', width=self.width, height=self.height, bd=0)
            self.frame.pack(fill=tk.BOTH, expand=1)
            self.canvas = tk.Canvas(self.frame, bg='black', width=self.width, height=self.height, bd=0, highlightthickness=0, relief='ridge')
            self.canvas.pack(fill=tk.BOTH, expand=1)

            self.root.attributes("-fullscreen", self.fullscreen)

            # controls
            self.root.bind("<F11>", self.toggle_fullscreen)
            self.root.bind("<z>", self.rand_index)
            self.root.bind("<q>", self.shuffle_sort)
            self.root.bind("<Left>", self.prev_index)
            self.root.bind("<Right>", self.next_index)
            self.root.bind("<space>", self.pause_play)
            self.root.bind("<Return>", self.next_index)
            self.root.bind("<Escape>", self.close_out)
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


    def show(self):
        # show
        if not self.paused:
            # remove preivous slide
            if self.slide:
                self.canvas.delete(self.slide)
    
            # get image for new slide
            img = Image.open(self.reel[self.index])
    
            # resize if necessary
            if self.zoomed:
                widthratio = float(self.width)/img.size[0]
                heightratio = float(self.height)/img.size[1]
                if widthratio < heightratio:
                    img = img.resize((int(self.width), int(img.size[1]*widthratio)), PIL.Image.ANTIALIAS)
                else:
                    img = img.resize((int(img.size[0]*heightratio), int(self.height)), PIL.Image.ANTIALIAS)

        # display slide
        self.photoimage = ImageTk.PhotoImage(img)
        self.canvas.pack()
        self.slide = self.canvas.create_image(self.width/2, self.height/2, image=self.photoimage)
        
        # increment index
        self.index = (self.index + 1) % len(self.reel)
        
    def showloop(self):
        self.show()
        # requeue in loop
        self.looperid = self.root.after(int(self.delay*1000), self.showloop)


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
        self.index = (self.index - 1) % len(self.reel)
        self.show()
        return "break"


    def rand_index(self, event=None):
        # randomize index
        self.index = randint(0,len(self.reel)-1)
        # reset loop
        if self.looperid:
            self.root.after_cancel(self.looperid)
        self.show()
        self.looperid = self.root.after(int(self.delay*1000), self.showloop)        
        return "break"


    def next_index(self, event=None):
        # reset loop
        if self.looperid:
            self.root.after_cancel(self.looperid)
        self.show()
        self.looperid = self.root.after(int(self.delay*1000), self.showloop)        
        return "break"


    def prev_index(self, event=None):
        # index already incremented, so decrement 2
        self.index = (self.index - 2) % len(self.reel)
        # reset loop
        if self.looperid:
            self.root.after_cancel(self.looperid)
        self.show()
        self.looperid = self.root.after(int(self.delay*1000), self.showloop)        
        return "break"

    def pause_play(self, event=None):
        self.paused = not self.paused
        return "break"


    def shuffle_sort(self, event=None):
        if self.shuffled:
            self.reel.sort()
        else:
            shuffle(self.reel)
        self.shuffled = not self.shuffled
        return "break"


    def close_out(self, event=None):
        try:
            self.root.destroy()
        except:
            pass
        return "break"

    
    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        self.width = event.width
        self.height = event.height
        self.index = (self.index - 1) % len(self.reel)
        self.show()
        

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('imagepath', 
        nargs='*',
        help='path to image or folder of images',
        default=['.'])
    parser.add_argument('-r', '--recursive',
        action='store_true',
        help='recurse though imagepath directory',
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
    args = parser.parse_args()

    # gc override
    args.recursive = True
    args.fullscreen = False
    args.zoomed = True
    args.delay = 12
    
    #print(args.imagepath)
    imagepaths = []
    for path in args.imagepath:
        imagepaths.extend(get_paths(path, args.recursive))
    #for i in imagepaths: print(i)
    imagepaths = images_only(imagepaths)
    #for i in imagepaths: print(i)

    sldshw = SlideShow(imagepaths, fullscreen=args.fullscreen, zoomed=args.zoomed, delay=args.delay)
