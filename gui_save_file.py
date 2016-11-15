from Tkinter import *
from tkFileDialog import *
import tkFileDialog

root=Tk("Text Editor")
text=Text(root)
text.grid()
def saveas():
    global text  
    t = text.get("1.0", "end-1c")
    savelocation=tkFileDialog.asksaveasfilename(defaultextension='.txt')
    file1=open(savelocation, "w+")
    file1.write(t)
    file1.close()
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
filemenu.add_command(label="Save", command=saveas)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
root.mainloop()