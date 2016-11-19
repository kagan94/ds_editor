import Tkinter, tkFileDialog, tkMessageBox, ttk
from Tkinter import *
from ScrolledText import *
from protocol import RESP


class GUI(object):
    previously_selected_file = None
    count = 0  # <- this var can be deleted later...

    def __init__(self, parent, client):
        '''
        :param parent: Tkinter object
        :param client: Client object
        '''

        self.root = parent
        self.client = client

        # load initial setting
        self.text = ScrolledText(self.root, width=70, height=30)
        self.text.grid(row=0, column=2)

        # Loading the list of files in menu
        self.files_list = Listbox(self.root, height=5)
        self.files_list.grid(column=0, row=0, sticky=(N, W, E, S))

        # Attach scroll to list of files
        self.scrollbar = ttk.Scrollbar(self.root, orient=VERTICAL, command=self.files_list.yview)
        self.scrollbar.grid(column=1, row=0, sticky=(N, S))
        self.files_list['yscrollcommand'] = self.scrollbar.set

        ttk.Sizegrip().grid(column=1, row=1, sticky=(S, E))
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.upload_list_of_accessible_files_into_menu()

        # Main menu in GUI ----------------------------------------------------------------------------
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.file_menu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.onFileCreation)
        self.file_menu.add_command(label="Open", command=self.onOpenFile)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.onExit)

        self.block_text_window()

        # Add triggers
        # Recognize any press on the keyboard and"Enter" press
        self.text.bind("<Key>", self.onKeyPress)
        self.text.bind("<Return>", self.onEnterPress)

        self.root.protocol('WM_DELETE_WINDOW', self.onExit)
        self.files_list.bind('<<ListboxSelect>>', self.onFileSelection)

    # Triggers in the GUI window ========================================================================
    # ========= Triggers in text area ===================================================================
    def get_index(self, index):
        return tuple(map(int, str(self.text.index(index)).split(".")))

    def onKeyPress(self, event):
        global count

        # self.count += 1
        #
        # if self.count == 5:
        #     self.text.insert(1.1, "click here!")
        c, pos = event.char, self.get_index("insert")

        if event.keysym == "BackSpace":
            print "backspace", pos

        elif event.keysym == "Delete":
            print "Delete pressed", pos

        elif c != "":
            print "pressed", c, pos, event.keysym

    def onEnterPress(self, event):
        c = event.char

        # "Enter" was pressed
        if c == "\r" or "\n":
            print repr("\n"), self.get_index("insert")
        else:
            print(c)

    # ========= Other triggers ==========================================================================
    def onFileSelection(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        selected_file = w.get(index)

        if selected_file and (not self.previously_selected_file or self.previously_selected_file != selected_file):

            print 'You selected item "%s"' % selected_file

            # Save/update opened file in local storage
            # TODO: save opened file and load requested file

            # Download requested file
            resp, content = self.client.get_file_on_server(selected_file)

            if resp == RESP.OK:
                self.unblock_text_window()

                # Update window
                self.replace_text(content)
                # self.upload_content_into_textfield(content)
            else:
                self.clear_text()
                self.block_text_window()
                print "Error occurred while tried to download file"

        self.previously_selected_file = selected_file

    def onFileCreation(self):
        file_name = "test.txt"

        # Create a new empty file
        with open(file_name, 'w'):
            pass

    def onOpenFile(self):
        tk_file = tkFileDialog.askopenfile(parent=root, mode='rb', title='Select a file')

        with open('test.txt','w') as f:
            f.write(self.text.get(1.0, END))

        if tk_file:
            contents = tk_file.read()
            self.upload_content_into_textfield(contents)
            tk_file.close()

    def onExit(self):
        # if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
        f = open('test.txt','w')
        f.write(self.text.get(1.0, END))
        f.close()
        self.root.destroy()

    # Functions to work with interface ==================================================================
    def compare_changes(self, text_1, text_2):
        '''
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

    def upload_list_of_accessible_files_into_menu(self):
        accessible_files = self.client.get_accessible_files()

        for filename in accessible_files:
            self.files_list.insert(END, filename)

    def get_text(self):
        contents = self.text.get(1.0, Tkinter.END)
        return contents

    def set_text(self, info):
        self.text.insert(END, info)

    def replace_text(self, content):
        self.clear_text()
        self.set_text(content)

    def clear_text(self):
        self.text.delete(1.0, "end")

    def block_text_window(self):
        self.text.config(state=DISABLED, background="gray")

    def unblock_text_window(self):
        self.text.config(state=NORMAL, background="white")