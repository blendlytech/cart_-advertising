import tkinter as tk
from tkinter import ttk
import sys
sys.path.append('c:/Users/DELL/cart_advertising/CartDialCRM')
from theme import apply_theme

root = tk.Tk()
style = ttk.Style(root)
style.theme_use('clam')
print("Default layout:", style.layout('TButton'))

apply_theme(root)
print("Applied layout:", style.layout('Primary.TButton'))
print("Primary Button config:", style.configure('Primary.TButton'))
print("Primary Button map:", style.map('Primary.TButton'))
