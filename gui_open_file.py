import Tkinter
import tkFileDialog
from Tkinter import *
from ScrolledText import *


def any_key_pressed(event):
    print "pressed", repr(event.char)


def enter_pressed(event):
    print "'enter' pressed", repr(event.char)


root = Tkinter.Tk(className="Text Editor")
text = ScrolledText(root, width=110, height=30)
text.grid()

# Recognize any press on the keyboard (only characters and backspace)
text.bind("<Key>", any_key_pressed)

# Recognize a "enter" press
text.bind("<Return>", enter_pressed)


def open():
    file = tkFileDialog.askopenfile(parent=root,mode='rb',title='Select a file')
    if file != None:
        contents = file.read()
        text.insert('1.0',contents)
        file.close()


menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Open", command=open)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)


root.mainloop()