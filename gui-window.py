import Tkinter, tkFileDialog, tkMessageBox
import ttk, os
from Tkinter import *
from ScrolledText import *

# Global variables
previously_selected_file = None
count = 0  # <- this var can be deleted later...


# Triggers in the GUI window ========================================================================
# ========= Triggers in text area ===================================================================
def get_index(text, index):
    return tuple(map(int, str(text.index(index)).split(".")))


def onKeyPress(event):
    global count

    # count += 1
    #
    # if count == 5:
    #     text.insert(1.1, "click here!")
    c, pos = event.char, get_index(text, "insert")

    if event.keysym == "BackSpace":
        print "backspace", pos

    elif event.keysym == "Delete":
        print "Delete pressed", pos

    elif c != "":
        print "pressed", c, pos, event.keysym


def onEnterPress(event):
    c = event.char

    # "Enter" was pressed
    if c == "\r" or "\n":
        print repr("\n"), get_index(text, "insert")
    else:
        print(c)

# ========= Other triggers ==========================================================================
def onFileSelection(event):
    global previously_selected_file

    w = event.widget
    index = int(w.curselection()[0])
    file_name = w.get(index)

    if not previously_selected_file or previously_selected_file != file_name:
        print 'You selected item "%s"' % file_name

        # TODO: save opened file and load requested file

        # if textfield's disable, then enable it after uploading file info
        text.config(state=NORMAL, background="white")

    previously_selected_file = file_name


def onFileCreation():
    file_name = "test.txt"

    # Create a new empty file
    with open(file_name, 'w'):
        pass


def onOpenFile():
    tk_file = tkFileDialog.askopenfile(parent=root, mode='rb', title='Select a file')

    with open('test.txt','w') as f:
        f.write(text.get(1.0, END))

    if tk_file:
        contents = tk_file.read()
        upload_content_into_textfield(contents)
        tk_file.close()


def onExit():
    # if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
    f = open('test.txt','w')
    f.write(text.get(1.0, END))
    f.close()
    root.destroy()


# Functions to work with interface ==================================================================
def upload_content_into_textfield(info):
    text.insert(1.0, info)


def content_from_textfield():
    contents = text.get(1.0, Tkinter.END)
    return contents


def compare_changes(text_1, text_2):
    '''
    Changes check by md5
    :param text_1: (string)
    :param text_2: (string)
    :return: (Boolean) True - if the texts are the same
    '''
    if text_1 == text_2:
        print "Information is the same"
    else:
        print "Information doesn't match!"

    # TODO: figure out which changes were made and show them to the user

    return text_1 == text_2


def upload_list_of_accessible_files_into_menu():
    path = os.path.dirname(os.path.realpath(__file__))
    files = os.listdir(path)

    for filename in files:
        files_list.insert(END, filename)


# Start GUI part ====================================================================================
root = Tkinter.Tk(className="Text Editor")
text = ScrolledText(root, width=70, height=30)
text.grid(row=0, column=2)


# Loading the list of files in menu
files_list = Listbox(root, height=5)
files_list.grid(column=0, row=0, sticky=(N, W, E, S))

# Attach scroll to list of files
scrollbar = ttk.Scrollbar(root, orient=VERTICAL, command=files_list.yview)
scrollbar.grid(column=1, row=0, sticky=(N, S))
files_list['yscrollcommand'] = scrollbar.set

ttk.Sizegrip().grid(column=1, row=1, sticky=(S, E))
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

upload_list_of_accessible_files_into_menu()


# Main menu in GUI ----------------------------------------------------------------------------
menu = Menu(root)
root.config(menu=menu)

file_menu = Menu(menu)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="New", command=onFileCreation)
file_menu.add_command(label="Open", command=onOpenFile)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=onExit)


# Blocking window, when the user launch the program firstly
text.config(state=DISABLED, background="gray")


# Add triggers
# Recognize any press on the keyboard and"Enter" press
text.bind("<Key>", onKeyPress)
text.bind("<Return>", onEnterPress)
root.protocol('WM_DELETE_WINDOW', onExit)
files_list.bind('<<ListboxSelect>>', onFileSelection)


root.mainloop()
