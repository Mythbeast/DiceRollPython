import random
import tkinter as tk
import configparser
import os
from tkinter import ttk
from PIL import ImageTk,Image

# NOTES
# rolling dice list updates every time but can only be changed by rolling scale spinbox - inefficient
# dice lists should be cached for reuse rather than created new every time - need to include size and colour
# add more UI elements including an RGB background selector
# currently config.ini needs to be manually updated to specify location of spritesheet

# Global constant
MS_PER_SECOND = 1000

class SpriteSheet():
    # class to handle loading and cropping of sprite sheets
    def __init__(self, location, sheet_width, sheet_height, sprite_width, sprite_height, rolling_dice_row):
        self.sprite_sheet_location = location
        self.sprite_sheet_width = sheet_width
        self.sprite_sheet_height = sheet_height
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.rolling_dice_row = rolling_dice_row
        self.sprite_sheet = Image.open(location).convert("RGBA")
        self.dice_colours = ['White', 'Dark purple', 'Red', 'Hot pink', 'Blush pink', 'Purple', 'Cyan', 'Dark blue', 'Green', 'Light green', 'Yellow', 'Orange']

    def crop_sprite_sheet(self, chosen_position, scale):
    # function to isolate sprites within a sprite sheet
        if (chosen_position[0])*self.sprite_width > self.sprite_sheet_width or (chosen_position[1])*self.sprite_height > self.sprite_sheet_height:
            print("ERROR: sprite outside of range")
            return None
        
        #where to find first sprite on sheet
        _x_start = (chosen_position[0]-1)*self.sprite_width
        _y_start = (chosen_position[1]-1)*self.sprite_height
        _x_end = (chosen_position[0])*self.sprite_width 
        _y_end = (chosen_position[1])*self.sprite_height 

        # crop sprite sheet to chosen sprite
        _sprite = self.sprite_sheet.crop((_x_start,_y_start,_x_end,_y_end))
        
        # enlarge sprite by scale factor
        _scale_factor = int(scale)
        _large_sprite = _sprite.resize(size=(self.sprite_width*_scale_factor,self.sprite_width*_scale_factor))
        return (_large_sprite)
    
    def get_colour_index(self, colour):
        return self.dice_colours.index(colour.get()) + 1


    
class Dice():
    # offset for rolling dice placement
    ROLLING_DISPLAY_OFFSET_X = 15
    ROLLING_DISPLAY_OFFSET_Y = 15
    # how many images in dice list
    NUM_IMAGES = 6
    # initial value of result scale spinbox
    INITIAL_SPINBOX_SCALE = 1.0
    def __init__(self, dice_colour, rolling_scale, result_scale, rolling_delay, result_delay, sprite_sheet):
        self.sprite_sheet = sprite_sheet
        self.result_delay = tk.DoubleVar(value=result_delay)
        self.original_rolling_scale = rolling_scale
        self.original_result_scale = result_scale
        self.rolling_scale = rolling_scale
        self.result_scale = result_scale
        # index used to display rolling dice images
        self.next_image_index = 0

        # combobox variables
        self.spinbox_scale = tk.DoubleVar(value=self.INITIAL_SPINBOX_SCALE)
        self.prev_spinbox_scale = self.INITIAL_SPINBOX_SCALE
        self.rolling_delay = tk.DoubleVar(value=rolling_delay)
        self.prev_spinbox_rolling_delay = rolling_delay
        self.result_delay = tk.DoubleVar(value=result_delay)
        self.prev_spinbox_result_delay = result_delay
        # spinbox variables
        self.dice_colour = dice_colour
        self.prev_colour = dice_colour.get()
        # creation of dice lists 
        self.dice_list = self.create_dice_list(sprite_sheet, self.sprite_sheet.get_colour_index(self.dice_colour), self.result_scale)
        self.rolling_dice_list = self.create_dice_list(sprite_sheet, self.sprite_sheet.rolling_dice_row, self.rolling_scale)
        # variables to handle cancelling roll result if rerolled
        self.future_clear = None
        self.future_create = None
 
    def create_dice_list(self, dice_sprite_sheet, dice_choice, scale):
    # creation of dice lists
        my_dice=[]
        for i in range(6):
            my_dice.append(ImageTk.PhotoImage(dice_sprite_sheet.crop_sprite_sheet((i+1,dice_choice), scale)))
        return(my_dice)
    
    def check_result_scale_spinbox(self):
    # function to check whether spinbox numbers have been changed
        _current_scale = self.spinbox_scale.get()
        if self.prev_spinbox_scale != _current_scale:
            self.result_scale = self.original_result_scale*_current_scale
            self.prev_spinbox_scale = _current_scale
            return True
        else: 
            return False
        
    def check_rolling_delay_spinbox(self):
    # function to check whether spinbox numbers have been changed
        _current_delay = self.rolling_delay.get()
        if self.prev_spinbox_rolling_delay != _current_delay:
            self.rolling_delay = _current_delay
            self.prev_spinbox_rolling_delay = _current_delay
            return True
        else:
            return False
        
    def check_result_delay_spinbox(self):
    # function to check whether spinbox numbers have been changed
        _current_delay = self.result_delay.get()
        if self.prev_spinbox_result_delay != _current_delay:
            self.result_delay = _current_delay
            self.prev_spinbox_result_delay = _current_delay
            return True
        else:
            return False
        
    def check_colour_spinbox(self):
    #  function to check whether combobox colour has changed
        _current_colour = self.dice_colour.get()
        if self.prev_colour != _current_colour:
            self.prev_colour = _current_colour
            return True
        else:
            return False

    def check_for_dice_change(self):
    # function to check whether any spinbox/combobox values have been changed and update dice
        if self.check_result_scale_spinbox() or self.check_rolling_delay_spinbox or self.check_colour_spinbox:
            self.update_dice()

    def update_dice(self):
    # function call to update dice on colour change or resize
        _colour_index = self.sprite_sheet.get_colour_index(self.dice_colour)
        self.dice_list = self.create_dice_list(self.sprite_sheet, _colour_index, self.result_scale)
        self.rolling_dice_list = self.create_dice_list(self.sprite_sheet, self.sprite_sheet.rolling_dice_row, self.rolling_scale)

    def multiply_rolling_scale(self, scale_factor):
    # function called on window resize
        self.rolling_scale = self.original_rolling_scale*scale_factor

    def multiply_result_scale(self, scale_factor):
    # function called on window resize
        self.result_scale = self.original_result_scale*scale_factor
    
    def show_next_image(self, canvas, sprite_sheet):
    # recursive function to show all rolling dice
    # TODO: Could compute these once and re-use them or cache them for reuse
        canvas.delete("all")
        # calculate size of dice on canvas
        _dice_size = sprite_sheet.sprite_width*self.rolling_scale

        # calculate size of each of the 5 gaps between the 6 images
        _interval = (canvas.winfo_width()- 2*canvas.bd - self.NUM_IMAGES*_dice_size)/(self.NUM_IMAGES-1)

        # calculate where to put the rolling dice on the canvas, accounting for gaps at edges, gaps between images and previously placed dice
        # brackets added for readability
        _x_offset = (self.ROLLING_DISPLAY_OFFSET_X) + (_dice_size*self.next_image_index) + (self.next_image_index*_interval)
        
        if self.next_image_index < len(self.rolling_dice_list)-1:
            canvas.create_image((_x_offset,self.ROLLING_DISPLAY_OFFSET_Y), anchor = 'nw', image=self.rolling_dice_list[self.next_image_index])
            canvas.after(int(MS_PER_SECOND*self.rolling_delay.get()), lambda: self.show_next_image(canvas, sprite_sheet))
            self.next_image_index += 1
        else:
            canvas.create_image((_x_offset,self.ROLLING_DISPLAY_OFFSET_Y), anchor = 'nw', image=self.rolling_dice_list[self.next_image_index])
            

    def roll(self, canvas, sprite_sheet):
        # Cancel previous roll operations if they exist and clear the canvas
        # TODO: currently this only removes the result dice, not any rolling animation
        canvas.delete("all")
        if self.future_clear:
            canvas.after_cancel(self.future_clear)
        if self.future_create:
            canvas.after_cancel(self.future_create)
        self.next_image_index = 0

        # check whether dice settings have changed and update dice
        self.check_for_dice_change()

        # create all dice images on canvas        
        dice_delay = self.rolling_delay.get()
        result_delay = self.result_delay.get()
        # show all rolling dice
        self.show_next_image(canvas, sprite_sheet)

        # choose result value
        n = random.randint(1,6)
        # find centre for placement
        _width = canvas.winfo_width()
        _height = canvas.winfo_height()
        _centre = (_width/2, _height/2)
        # clear final rolling dice and place result die
        self.future_clear = canvas.after(int(MS_PER_SECOND*dice_delay*self.NUM_IMAGES+ MS_PER_SECOND*result_delay - 1), lambda: canvas.delete("all"))
        self.future_create = canvas.after(int(MS_PER_SECOND*dice_delay*self.NUM_IMAGES + MS_PER_SECOND*result_delay), lambda: canvas.create_image(_centre, anchor = 'center', image=self.dice_list[n-1]))

class ResizingCanvas(tk.Canvas):
    # canvas which causes dice lists to be scaled when window expands
    def __init__(self,parent, dice, **kwargs):
        super().__init__(parent)
        self.bind("<Configure>", self.on_resize)
        self.bd = kwargs.get("bd")
        self.bg = kwargs.get("bg")
        self.relief = kwargs.get("relief")
        self.highlightthickness = kwargs.get("highlightthickness")
        self.cursor = kwargs.get("cursor")
        self.dice = dice
        self.scale_factor = 1
        self.last_resize_time = None
        self.resize_delay = 100

        # Configure Canvas
        self.config(bg=self.bg, bd=self.bd, relief=self.relief, highlightthickness=self.highlightthickness, cursor=self.cursor)
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.prev_width = self.winfo_width()
        self.prev_height = self.winfo_height()

    def on_resize(self, event):
        if self.last_resize_time:
            self.after_cancel(self.last_resize_time)
        self.width = event.width
        self.last_resize_time = self.after(self.resize_delay, self.resize_images)

    def resize_images(self):
        self._scale_factor = float(self.width) / 500
        self.dice.multiply_rolling_scale(self._scale_factor)
        self.dice.multiply_result_scale(self._scale_factor)
        self.dice.update_dice()

def initial_set_up(root):
    # create config object and read correct file
    config = configparser.ConfigParser()
    config_file_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config.read(config_file_path)

    define_window(root, config)
    dice_sheet = load_sprite_sheet_and_dice(config)
    return dice_sheet

def define_window(root, config):
    # function to read window info from config.ini

    # read info for window
    title = config['WINDOW']['title']
    width=config['WINDOW']['width']
    height=config['WINDOW']['height']
    minw=config['WINDOW']['minw']
    maxw=config['WINDOW']['maxw']
    minh=config['WINDOW']['minh']
    maxh=config['WINDOW']['maxh']
    # configure window limits and size
    
    root.title(title)
    size = str(width) + "x" + str(height)
    root.geometry(size)
    root.minsize(minw,minh)
    root.maxsize(maxw,maxh)
    
def load_sprite_sheet_and_dice(config):
    # function to read sprite sheet info from config.ini
    
    # read info for spritesheet
    dice_sprite_sheet_location = config['SPRITESHEET']['dice_sprite_sheet_location']
    sheet_width = int(config['SPRITESHEET']['sheet_width'])
    sheet_height = int(config['SPRITESHEET']['sheet_height'])
    sprite_width = int(config['SPRITESHEET']['sprite_width'])
    sprite_height = int(config['SPRITESHEET']['sprite_height'])
    rolling_dice_row = int(config['SPRITESHEET']['rolling_dice_row'])
    # load the sprite sheet
    dice_sheet = SpriteSheet(dice_sprite_sheet_location, sheet_width, sheet_height, sprite_width, sprite_height, rolling_dice_row)

    # read info for dice
    rolling_scale = int(config['DICE']['rolling_scale'])
    result_scale = int(config['DICE']['result_scale'])
    rolling_delay =config['DICE']['rolling_delay']
    result_delay = config['DICE']['result_delay']

    original_colour = tk.StringVar(value=dice_sheet.dice_colours[0])
    my_dice = Dice(original_colour, rolling_scale, result_scale, rolling_delay, result_delay ,sprite_sheet=dice_sheet)

    return (dice_sheet, my_dice, original_colour)
    
def load_UI_elements(root, my_dice, dice_sheet, original_colour):
    # creation of frame for UI elements
    my_frame = tk.Frame(root)
    my_frame.pack(side="top", fill = "both", expand=True, padx=10, pady=10)
    # configure rows and columns of frame
    my_frame.grid_rowconfigure(0, weight=1)
    my_frame.grid_columnconfigure(0, weight=1) 
   
    # creation of UI elements
    canvas_border_size = 10
    my_canvas = ResizingCanvas(my_frame, my_dice, width=400 - 2*canvas_border_size, height = 350, bd=canvas_border_size, relief='ridge', highlightthickness=0, bg = 'skyblue', cursor='dot')
    my_button = tk.Button(my_frame, text = "Roll the dice?", command = lambda:my_dice.roll(my_canvas, dice_sheet))

    colour_label = tk.Label(my_frame, text = "Dice Colour:")
    dice_colour_box = ttk.Combobox(my_frame, values=dice_sheet.dice_colours, textvariable=original_colour)

    spinbox_scale_label = tk.Label(my_frame, text = "Result Size:")
    result_scale_spinbox = tk.Spinbox(my_frame, from_=0.1, to = 5.0, textvariable=my_dice.spinbox_scale, increment=0.1)

    spinbox_result_delay_label = tk.Label(my_frame, text = "Result Delay:")
    result_delay_spinbox = tk.Spinbox(my_frame, from_=0.01, to = 5.00, textvariable=my_dice.result_delay, increment=0.01)

    spinbox_rolling_delay_label = tk.Label(my_frame, text = "Rolling Delay:")
    rolling_delay_spinbox = tk.Spinbox(my_frame, from_=0.01, to = 5.00, textvariable=my_dice.rolling_delay, increment=0.01)

    # load UI elements into frame
    my_canvas.grid(row=0, column = 0, columnspan = 4, sticky = 'nsew')
    my_button.grid(row=1, column = 0, rowspan = 2, sticky = 'nsew')

    colour_label.grid(row=1, column = 2)
    dice_colour_box.grid(row=1, column = 3)
    
    spinbox_scale_label.grid(row=2, column = 2)
    result_scale_spinbox.grid(row = 2, column=3)
    
    spinbox_result_delay_label.grid(row=3, column = 2)
    result_delay_spinbox.grid(row=3, column = 3)

    spinbox_rolling_delay_label.grid(row=4, column = 2)
    rolling_delay_spinbox.grid(row=4, column = 3)

def main():
    root = tk.Tk()
        
    # configure window, load spritesheet and dice
    (dice_sheet,my_dice, original_colour) = initial_set_up(root)
    
    # load frame, all UI elements and arrange them in the window
    load_UI_elements(root, my_dice, dice_sheet, original_colour)
    
    root.mainloop()

if __name__ == "__main__":
    main()
    