import Tkinter
import string
import hashlib
import tkFileDialog
from Tkinter import *
from ScrolledText import *

count = 0

def getindex(text, index):
    return tuple(map(int, string.split(text.index(index), ".")))

def any_key_pressed(event):
    global count

    # print getindex(text, "end")

    # count += 1
    #
    # if count == 5:
    #     text.insert(1.1, "click here!")
    c = event.char

    if event.keysym == "BackSpace":
        print "backspace", getindex(text, "insert")

    elif event.keysym == "Delete":
        print "Delete pressed", getindex(text, "insert")


    # These 2 don't work now..
    elif event.keysym == "z":
        text.edit_undo()
    elif event.keysym == "y":
        text.edit_redo()

    print text.edit_modified()

    print repr(c), event.keysym
    # if event.char != "":
    #     print "pressed", repr(event.char)
    #
    #     print getindex(text, "insert")


    # TODO: User deletes the selected region


def enter_pressed(event):
    c = event.char

    # "Enter" was pressed
    if c == "\r" or "\n":
        print repr("\n"), getindex(text, "insert")

    # else:
    #     print(c)

def upload_whole_info_into_textfield(info):
    text.insert(1.0, info)


def get_all_content_from_textfield():
    contents = text.get(1.0, Tkinter.END)
    return contents


def compare_changes(text_1, text_2):
    '''
    Changes check by md5
    :param text_1: (string)
    :param text_2: (string)
    :return:
    '''

    def get_signature(contents):
        return hashlib.md5(contents).digest()

    if get_signature(text_1) == get_signature(text_2):
        print "Information is the same"
    else:
        print "Information doesn't match!"

    # TODO: figure out which changes were made and show them to the user

    return get_signature(text_1) == get_signature(text_2)




# def backspace(event):
#     print event.widget.delete("%s-1c" % INSERT, INSERT)



root = Tkinter.Tk(className="Text Editor")
text = ScrolledText(root, width=70, height=30)
# text = ScrolledText(root, width=110, height=30)
text.grid()


# Recognize any press on the keyboard (only characters and backspace)
text.bind("<Key>", any_key_pressed)
# text.bind("<BackSpace>", backspace)




# Recognize a "enter" press
text.bind("<Return>", enter_pressed)


upload_whole_info_into_textfield("some info...")


compare_changes("1111", "1111")


# Blocking window, when the user launch the program firstly
text.config(state=DISABLED, background="gray")
text.config(state=NORMAL, background="white")



root.mainloop()