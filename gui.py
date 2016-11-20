import Tkinter, tkFileDialog, tkMessageBox, ttk, os
from Tkinter import *
from ScrolledText import *
from protocol import RESP, CHANGE_TYPE, parse_change, error_code_to_string
import tkSimpleDialog, difflib


# local copies of files on the client side
current_path = os.path.abspath(os.path.dirname(__file__))
dir_local_files = os.path.join(current_path, "client_local_files")


class DialogAskFileName(tkSimpleDialog.Dialog):
    ''' Window that asks user to type new file name and its access '''
    def body(self, master):
        self.root = master
        self.file_name = None

        Label(master, text="File name").grid(row=1, sticky=W)
        self.name = Entry(master)
        self.name.grid(row=1, column=1)

        instructions = Label(master, text="Make file private?").grid(row=0)
        self.answer_return = IntVar()
        self.answer = Checkbutton(master, variable=self.answer_return)
        self.answer.grid(row=0, column=1)

    def apply(self):
        self.access = (self.answer_return.get())
        self.file_name = (self.name.get())


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
        self.text = ScrolledText(self.root, width=50, height=15)
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

        # Status
        self.status = StringVar()
        self.label = Label(self.root, textvariable=self.status)
        self.set_notification_status("-")

        self.label.grid(column=0, columnspan=2, sticky=(W))

        # Button check changes
        btn = Button(self.root, text="Check Changes")
        btn.grid(column=2, row=2, sticky=(E))
        # TODO: create a new window on click if there'we some changes

        # Main menu in GUI ----------------------------------------------------------------------------
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.menu.add_command(label="New file", command=self.onFileCreation)
        # self.menu.add_command(label="Open", command=self.onOpenFile)
        self.menu.add_command(label="Exit", command=self.onExit)

        # Update list of accessible files
        self.upload_list_of_accessible_files_into_menu()

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
        current_file = self.selected_file()
        # inserted character and position of change
        char, pos_change = event.char, str(self.text.index("insert"))

        # If any file was chosen
        if current_file:
            # self.count += 1
            # if self.count == 5:
            #     self.text.insert(1.1, "click here!")
            # c, pos = event.char, self.get_index("insert")

            if event.keysym == "BackSpace":
                self.client.update_file_on_server(current_file, CHANGE_TYPE.BACKSPACE, pos_change)
                print "backspace", pos_change

            elif event.keysym == "Delete":
                self.client.update_file_on_server(current_file, CHANGE_TYPE.DELETE, pos_change)
                print "Delete pressed", pos_change
                # self.text.delete(float(pos_change[0]) + .1)

            elif char != "" and event.keysym != "Escape":
                self.client.update_file_on_server(current_file, CHANGE_TYPE.INSERT, pos_change, key=char)
                print "pressed", char, pos_change, event.keysym


    def onEnterPress(self, event):
        current_file = self.selected_file()

        # If any file was chosen
        if self.selected_file():
            char, pos_change = event.char, str(self.text.index("insert"))

            # "Enter" was pressed
            if char in ["\r", "\n"]:
                self.client.update_file_on_server(current_file, CHANGE_TYPE.ENTER, pos_change)
                print repr("\n"), self.get_index("insert")
            else:
                print(char)

    # ========= Other triggers ==========================================================================
    def onFileSelection(self, event):
        selected_file = self.selected_file()

        if selected_file and (not self.previously_selected_file or self.previously_selected_file != selected_file):
            # Update notification bar
            self.set_notification_status("selected file " + selected_file)

            # Save previously opened text file in local storage
            self.save_opened_text()

            # Download selected file
            resp_code, content = self.client.get_file_on_server(selected_file)

            # Case: File was successfully downloaded
            if resp_code == RESP.OK:
                # Unblock and update text window
                self.unblock_text_window()
                self.replace_text(content)

                # Check whether the local copy was changed or not
                self.compare_local_copy_with_origin(local_file_name=selected_file, original_text=content)

            # Case: Error response from server on file downloading
            else:
                self.clear_text()
                self.block_text_window()

            # Update notification bar
            self.set_notification_status("download file", resp_code)
            # print "Error occurred while tried to download file"

        self.previously_selected_file = selected_file

    def onFileCreation(self):
        ask_file_dialog = DialogAskFileName(self.root)

        # Fetch values from Dialog form
        file_name = ask_file_dialog.file_name

        # Check if the user didn't press cancel
        if file_name:
            access = str(ask_file_dialog.access)  # Private(1) or Public(0)

            # Send request to server to create file
            resp_code = self.client.create_new_file(file_name, access)

            if resp_code == RESP.OK:
                self.save_opened_text()

                # Create a new empty file
                with open(file_name, 'w'):
                    pass

                self.files_list.insert(END, file_name)

            # Update notification bar
            self.set_notification_status("File creation", resp_code)

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
        # save opened text in window
        self.save_opened_text()
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
        resp_code, accessible_files = self.client.get_accessible_files()
        # accessible_files = []
        # resp_code = 0

        for filename in accessible_files:
            self.files_list.insert(END, filename)

        # Update notification bar
        self.set_notification_status("List of files", resp_code)

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

    def selected_file(self):
        widget = self.files_list

        try:
            index = int(widget.curselection()[0])
            selected_file = widget.get(index)
        except:
            selected_file = None

        return selected_file

    def set_notification_status(self, message, err_code=None):
        if err_code:
            message += ".\n" + error_code_to_string(err_code)

        self.status.set("Last action: " + message)

    #  =========================================================================
    def update_from_another_client(self, change):
        '''
        Another client made the change => update text window
        :param change: (string) in format
        '''

        # Parse change that arrived from server
        # position is in format "row.column"
        file_to_change, change_type, pos, key = parse_change(change)

        # And check whether the selected file matches with file in change
        selected_file = self.selected_file()

        if selected_file and selected_file == file_to_change:
            # Depending on change, do the change

            if change_type == CHANGE_TYPE.DELETE:
                self.text.delete(pos)

            elif change_type == CHANGE_TYPE.BACKSPACE:
                splitted_pos = pos.split(".")
                row, column = int(splitted_pos[0]), int(splitted_pos[1])

                if row - 1 > 0 and column == 0:
                    # Get last index in previous line, and delete it
                    pr_pos = str(row - 1) + ".0"
                    pr_line_last_len = len(self.text.get(pr_pos, pos))
                    last_index = str(row - 1) + "." + str(pr_line_last_len)

                    self.text.delete(last_index)
                elif column > 0:
                    pos_to_del = str(row) + "." + str(column - 1)
                    self.text.delete(pos_to_del)

            elif change_type == CHANGE_TYPE.ENTER:
                self.text.insert(pos, "\n")

            elif change_type == CHANGE_TYPE.INSERT:
                self.text.insert(pos, key)

            # print file_to_change, change_type, pos, key

            self.set_notification_status("another user changed the file")
