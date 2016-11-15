import Tkinter
from Tkinter import * 
import tkFileDialog

root = Tkinter.Tk(className="Text Editor")
text=Text(root) 
text.grid()

def open():
    file = tkFileDialog.askopenfile(parent=root,mode='rb',title='Select a file')
    if file != None:
        contents = file.read()
        text.insert('1.0',contents)
        file.close() 
def FontHelvetica():
   global text
   text.config(font="Helvetica")
def FontCourier():
    global text
    text.config(font="Courier")
font=Menubutton(root, text="Font") 
font.grid() 
font.menu=Menu(font, tearoff=0) 
font["menu"]=font.menu
helvetica=IntVar() 
courier=IntVar()
font.menu.add_checkbutton(label="Courier", variable=courier,
command=FontCourier)
font.menu.add_checkbutton(label="Helvetica", variable=helvetica, 
command=FontHelvetica)
menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Open", command=open)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
root.mainloop()