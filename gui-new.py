import Tkinter
import tkFileDialog
import tkMessageBox
from Tkinter import *
from ScrolledText import *
import ttk
import os
import sys

def get_filenames():
    path = os.path.dirname(os.path.realpath(__file__))
    return os.listdir(path)
	
def any_key_pressed(event):
    print "pressed", repr(event.char)

def enter_pressed(event):
    print "'enter' pressed", repr(event.char)

def new_file():
    name="test.txt"
    f = open("test.txt",'a')
    f.close()

def save_file():
    f = open('test.txt','w')
    f.write(text.get(1.0, END))
    f.close()
def save_file_as():
    savelocation=tkFileDialog.asksaveasfilename()
    f = open(savelocation, "w+")
    f.write(text.get(1.0, END))
    f.close()

def open_file():
    file = tkFileDialog.askopenfile(parent=root,mode='rb',title='Select a file')
    f = open('test.txt','w')
    f.write(text.get(1.0, END))
    f.close()
    if file != None:
        contents = file.read()
        text.insert('1.0',contents)
        file.close()
def exit():
    if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
        f = open('test.txt','w')
        f.write(text.get(1.0, END))
        f.close()
        root.destroy()

root = Tkinter.Tk(className="Text Editor")
text = ScrolledText(root, width=110, height=50)
text.grid(row = 0, column = 2)
filename = "Untitled.txt"
root.protocol('WM_DELETE_WINDOW', exit)

# Recognize any press on the keyboard (only characters and backspace)
text.bind("<Key>", any_key_pressed)

# Recognize a "enter" press
text.bind("<Return>", enter_pressed)

#list files in directory
l = Listbox(root, height=5)
l.grid(column=0, row=0, sticky=(N,W,E,S))
s = ttk.Scrollbar(root, orient=VERTICAL, command=l.yview)
s.grid(column=1, row=0, sticky=(N,S))
l['yscrollcommand'] = s.set
ttk.Sizegrip().grid(column=1, row=1, sticky=(S,E))
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
for filename in get_filenames ():
    l.insert(END, filename)

menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="New", command=new_file)
filemenu.add_command(label="Open", command=open_file)
filemenu.add_command(label="Save", command=save_file)
filemenu.add_command(label="Save As", command=save_file_as)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit)

root.mainloop()