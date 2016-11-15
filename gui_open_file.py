import Tkinter
from Tkinter import * 
import tkFileDialog


def key(event):
    print "pressed", repr(event.char)


root = Tkinter.Tk(className="Text Editor")
text=Text(root)
text.grid()


text.bind("<Key>", key)


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