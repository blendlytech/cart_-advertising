"""Shared desktop theme. Color roles documented in DESIGN.md."""
from tkinter import ttk

COLORS = {
    'background': '#edf2f7', 'surface': '#ffffff', 'ink': '#172c45',
    'muted': '#52657a', 'navy': '#112b46', 'navy_hover': '#1e4163',
    'teal': '#087f83', 'teal_hover': '#066568', 'border': '#c8d4e0',
    'stripe': '#f4f7fb', 'blue': '#285ea7', 'green': '#146745',
    'red': '#a33246', 'gold': '#f3c475', 'disabled': '#dce4eb',
    'header_text': '#d6e3ef', 'teal_tint': '#e3f5f1', 'blue_tint': '#e7effc',
    'gold_tint': '#fff3dc', 'gold_ink': '#805219', 'white': '#ffffff',
}

def apply_theme(root):
    c = COLORS
    root.configure(background=c['background'])
    root.option_add('*Text.background',c['surface'])
    root.option_add('*Text.foreground',c['ink'])
    root.option_add('*Text.insertBackground',c['teal'])
    root.option_add('*Text.selectBackground',c['navy'])
    root.option_add('*Text.selectForeground',c['white'])
    root.option_add('*Text.relief','flat')
    root.option_add('*Text.highlightThickness',1)
    root.option_add('*Text.highlightBackground',c['border'])
    root.option_add('*Text.highlightColor',c['teal'])
    root.option_add('*TCombobox*Listbox.background',c['surface'])
    root.option_add('*TCombobox*Listbox.foreground',c['ink'])
    root.option_add('*TCombobox*Listbox.selectBackground',c['navy'])
    root.option_add('*TCombobox*Listbox.selectForeground',c['white'])
    style=ttk.Style(root); style.theme_use('clam')
    style.configure('.',font=('Segoe UI',10),background=c['background'],foreground=c['ink'])
    style.configure('TLabel',background=c['background'],foreground=c['ink'])
    style.configure('Muted.TLabel',foreground=c['muted'])
    style.configure('Title.TLabel',font=('Segoe UI',23,'bold'),foreground=c['navy'])
    style.configure('TButton',padding=(12,8),background=c['surface'],foreground=c['ink'],bordercolor=c['border'],lightcolor=c['surface'],darkcolor=c['surface'],focuscolor=c['teal'])
    style.map('TButton',background=[('disabled',c['disabled']),('pressed',c['blue_tint']),('active',c['stripe'])],foreground=[('disabled',c['muted'])],bordercolor=[('focus',c['teal'])])
    for name,base,hover in [('Primary',c['teal'],c['teal_hover']),('Navy',c['navy'],c['navy_hover'])]:
        style.configure(name+'.TButton',font=('Segoe UI',10,'bold'),background=base,foreground=c['white'],bordercolor=base,lightcolor=base,darkcolor=base,focuscolor=c['gold'])
        style.map(name+'.TButton',background=[('disabled',c['disabled']),('pressed',hover),('active',hover)],foreground=[('disabled',c['muted']),('!disabled',c['white'])],bordercolor=[('focus',c['gold'])])
    for name in ['TEntry','TCombobox']:
        style.configure(name,padding=(6,3),fieldbackground=c['surface'],background=c['surface'],foreground=c['ink'],bordercolor=c['border'],lightcolor=c['surface'],darkcolor=c['surface'],arrowcolor=c['navy'])
        style.map(name,bordercolor=[('focus',c['teal'])],fieldbackground=[('readonly',c['surface'])],foreground=[('readonly',c['ink'])],selectbackground=[('focus',c['navy'])],selectforeground=[('focus',c['white'])])
    style.configure('Treeview',rowheight=36,background=c['surface'],fieldbackground=c['surface'],foreground=c['ink'],bordercolor=c['border'],lightcolor=c['border'],darkcolor=c['border'])
    style.map('Treeview',background=[('selected',c['navy'])],foreground=[('selected',c['white'])])
    style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=(10,10),background=c['navy'],foreground=c['white'],bordercolor=c['navy'],lightcolor=c['navy'],darkcolor=c['navy'])
    style.map('Treeview.Heading',background=[('active',c['navy_hover'])])
    style.configure('TNotebook',background=c['background'],borderwidth=0)
    style.configure('TNotebook.Tab',padding=(18,10),background=c['disabled'],foreground=c['muted'])
    style.map('TNotebook.Tab',background=[('selected',c['navy']),('active',c['blue_tint'])],foreground=[('selected',c['white']),('active',c['ink'])])
    for name in ['Vertical.TScrollbar','Horizontal.TScrollbar']:
        style.configure(name,background=c['border'],troughcolor=c['background'],arrowcolor=c['navy'],bordercolor=c['background'])
        style.map(name,background=[('active',c['muted']),('pressed',c['teal'])])
    return style
