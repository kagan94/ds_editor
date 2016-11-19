import Tkinter, tkFileDialog, tkMessageBox, ttk, os
from Tkinter import *
from ScrolledText import *
from protocol import RESP
import difflib

# local copies of files on the client side
current_path = os.path.abspath(os.path.dirname(__file__))
dir_local_files = os.path.join(current_path, "client_local_files")


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
        # self.file_menu.add_command(label="Open", command=self.onOpenFile)
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

            # Save previously opened text file in local storage
            self.save_opened_text()

            # Download selected file
            resp, content = self.client.get_file_on_server(selected_file)

            # Case: File was successfully downloaded
            if resp == RESP.OK:
                # Unblock and update text window
                self.unblock_text_window()
                self.replace_text(content)

                # Check whether the local copy was changed or not
                self.compare_local_copy_with_origin(local_file_name=selected_file, original_text=content)

            # Case: Error response from server on file downloading
            else:
                self.clear_text()
                self.block_text_window()
                print "Error occurred while tried to download file"

        self.previously_selected_file = selected_file

    def onFileCreation(self):
        file_name = "test.txt"

        access = 1 # Private
        access = 0 # Public

        # TODO: connect msg box with file name and checkbox to this function

        resp_code = self.client.create_new_file(file_name, access)

        if resp_code == RESP.OK:
            self.save_opened_text()

            # Create a new empty file
            with open(file_name, 'w'):
                pass

            self.files_list.insert(END, file_name)
        else:
            print "Error happened with file creation. (code: %s)" % resp_code
    # def onOpenFile(self):
    #     tk_file = tkFileDialog.askopenfile(parent=root, mode='rb', title='Select a file')
    #
    #     with open('test.txt','w') as f:
    #         f.write(self.text.get(1.0, END))
    #
    #     if tk_file:
    #         contents = tk_file.read()
    #         self.upload_content_into_textfield(contents)
    #         tk_file.close()

    def onExit(self):
        # if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
        f = open('test.txt','w')
        f.write(self.text.get(1.0, END))
        f.close()
        self.root.destroy()

    # Functions to work with interface ==================================================================
    def compare_local_copy_with_origin(self, local_file_name, original_text):
        '''
        :param local_file_name: File that may locate on the client side
        :param original_text: original content on the server
        :return: (Boolean) True - if the texts are the same
        '''
        local_file_path = os.path.join(dir_local_files, local_file_name)

        # If local copy of the file exists, then compare copies
        if os.path.isfile(local_file_path):
            with open(local_file_path, "r") as lf:
                local_content = lf.read()

            if local_content == original_text:
                print "Information is the same"

            else:
                print "Information doesn't match!"

                local_content, original_text = local_content.strip().splitlines(), original_text.strip().splitlines()

                for line in difflib.unified_diff(local_content, original_text, lineterm=''):
                    print line

                # TODO: show changes between local copy and download file in GUI

        else:
            print "Local copy was not found"

    def upload_list_of_accessible_files_into_menu(self):
        accessible_files = self.client.get_accessible_files()

        for filename in accessible_files:
            self.files_list.insert(END, filename)

    # Save previously opened text file in local storage
    def save_opened_text(self):
        if self.previously_selected_file is not None:
            ps_file_path = os.path.join(dir_local_files, self.previously_selected_file)

            with open(ps_file_path, "w") as f:
                content = self.get_text()
                f.write(content)

    def get_text(self):
        contents = self.text.get(1.0, Tkinter.END)

        # Tkinter adds \n in the text field. That's why we should deduct it.
        contents = contents[:len(contents) - len("\n")]
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