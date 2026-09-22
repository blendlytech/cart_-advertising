import tkinter as tk
from tkinter import ttk
import sys
sys.path.append('c:/Users/DELL/cart_advertising/CartDialCRM')
from theme import apply_theme, COLORS
from PIL import ImageGrab
import time

root = tk.Tk()
root.geometry('400x200')
apply_theme(root)

frame = ttk.Frame(root, padding=20)
frame.pack(fill='both', expand=True)

ttk.Button(frame, text='Save lead', style='Primary.TButton').pack(pady=5)
ttk.Button(frame, text='Call with TextNow', style='Navy.TButton').pack(pady=5)
ttk.Button(frame, text='Close').pack(pady=5)

root.update()
time.sleep(1)

# Take screenshot of the window
x = root.winfo_rootx()
y = root.winfo_rooty()
w = root.winfo_width()
h = root.winfo_height()
ImageGrab.grab(bbox=(x, y, x+w, y+h)).save('test_buttons.png')
root.destroy()
