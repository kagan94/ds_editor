#! /usr/bin/env python
# -*- coding: utf-8 -*-

import Tkinter, tkFileDialog, tkMessageBox, ttk, os
from Tkinter import *
from ScrolledText import *
from protocol import RESP, CHANGE_TYPE, parse_change, error_code_to_string, client_files_dir, \
                     ACCESS
import tkSimpleDialog, difflib


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
    selected_file = None
    file_changes = ""

    def __init__(self, parent, client):
        '''
        :param parent: Tkinter object
        :param client: Client object
        '''

        self.root = parent
        self.client = client

        # load initial setting
        self.text = ScrolledText(self.root, width=50, height=15)
        self.text.grid(row=0, column=2, columnspan=3)

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

        # Radio button to choose "Access"
        self.label.grid(column=0, columnspan=2, sticky=(W))
        self.access_button_val = StringVar()
        self.public_access = Radiobutton(self.root, text="Make file public", variable=self.access_button_val,
                                         value="0", state=DISABLED, command=self.onAccessChange)
        self.private_access = Radiobutton(self.root, text="Make file private", variable=self.access_button_val,
                                          value="1", state=DISABLED, command=self.onAccessChange)
        self.public_access.grid(column=2, row=2, sticky=(E))
        self.private_access.grid(column=3, row=2, sticky=(E))

        # Button check changes
        self.button_check_changes = Button(self.root, text="Check Changes", command=self.onCheckChanges)
        self.button_check_changes.grid(column=4, row=2, sticky=(E))

        # Main menu in GUI ----------------------------------------------------------------------------
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.menu.add_command(label="New file", command=self.onFileCreation)
        # self.menu.add_command(label="Open", command=self.onOpenFile)
        self.menu.add_command(label="Delete file", state=DISABLED, command=self.onFileDeletion)
        self.menu.add_command(label="Exit", command=self.onExit)

        # Update list of accessible files (request to server)
        self.upload_list_of_accessible_files_into_menu()

        # Start triggers for the first launch
        self.block_text_window()
        self.block_button_check_changes()

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
        current_file = self.selected_file
        # inserted character and position of change
        char, pos_change = event.char, str(self.text.index("insert"))

        # char = char.encode('utf-8')

        print repr(char)
        char = char.encode('utf-8')
        print repr(char)

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
        current_file = self.selected_file

        # If any file was chosen
        if current_file:
            char, pos_change = event.char, str(self.text.index("insert"))

            # "Enter" was pressed
            if char in ["\r", "\n"]:
                self.client.update_file_on_server(current_file, CHANGE_TYPE.ENTER, pos_change)
                print repr("\n"), self.get_index("insert")
            else:
                print(char)


    # ========= Other triggers ==========================================================================
    def onFileSelection(self, event):
        # Get currently selected file
        widget = self.files_list
        try:
            index = int(widget.curselection()[0])
            selected_file = widget.get(index)
        except:
            selected_file = None

        if selected_file and (not self.selected_file or self.selected_file != selected_file):
            # Update notification bar
            self.set_notification_status("selected file " + selected_file)

            # Save previously opened text file in local storage
            self.save_opened_text()

            # Download selected file
            resp_code, response_data = self.client.get_file_on_server(selected_file)

            # Split additional arguments
            am_i_owner, file_access, content = response_data

            # Freeze delete and access buttons
            self.block_delete_button()
            self.block_access_buttons()

            # Case: File was successfully downloaded
            if resp_code == RESP.OK:
                # If I'm owner, then I can delete file and change its access
                if am_i_owner == "1":
                    self.release_delete_button()
                    self.choose_access_button(file_access)
                    self.chosen_access = file_access

                # Unblock and update text window
                self.unblock_text_window()
                self.replace_text(content)

                # Check and write changes in the file (prepare them)
                # When user clicks on the button, then these changes will be shown in the window)
                self.compare_local_copy_with_origin(selected_file, original_text=content)
                self.unblock_button_check_changes()

            # Case: Error response from server on file downloading
            else:
                self.clear_text()
                self.block_text_window()

            # Update notification bar
            self.set_notification_status("download file", resp_code)
            # print "Error occurred while tried to download file"

            self.selected_file = selected_file

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

                # add new file to the list
                self.files_list.insert(END, file_name)

                # Choose access button and activate delete button
                self.release_delete_button()
                self.choose_access_button(access)

            # Update notification bar
            self.set_notification_status("File creation", resp_code)

    # Trigger on switching between access buttons
    def onAccessChange(self):
        curent_access = self.access_button_val.get()
        file_name = self.selected_file

        # Request to the server to change access to the file
        if self.chosen_access != curent_access:
            resp_code = self.client.change_access_to_file(file_name, self.chosen_access)

            self.set_notification_status("change access to file " + str(file_name), resp_code)
        self.chosen_access = curent_access

    # Trigger on file deletion button
    def onFileDeletion(self):
        # Send request to server to delete file
        file_name = self.selected_file

        resp_code = self.client.delete_file(file_name)

        # Block window, until user will select the file
        if resp_code == RESP.OK:
            self.remove_file_from_menu_and_delete_local_copy(file_name)

        # Update notification bar
        self.set_notification_status("file deletion", resp_code)

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

    def onCheckChanges(self):
        window = Toplevel(self.root)
        changes_window = ScrolledText(window, width=50, height=15, state="normal")
        changes_window.grid(row=0, column=0)

        # Clear, rewrite and show changes between opened and downloaded file
        changes_window.delete(1.0, "end")
        changes_window.insert(END, self.file_changes)

    def onExit(self):
        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
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
        local_file_path = os.path.join(client_files_dir, local_file_name)

        # If local copy of the file exists, then compare copies
        if os.path.isfile(local_file_path):
            with open(local_file_path, "r") as lf:
                local_content = lf.read()

            if local_content == original_text:
                self.file_changes = "Information is the same as in local copy"

            else:
                self.file_changes = "Information doesn't match!\n"

                local_content, original_text = local_content.strip().splitlines(), original_text.strip().splitlines()

                # Write mismatches and mismatches
                for line in difflib.unified_diff(local_content, original_text, lineterm=''):
                    self.file_changes += line + "\n"

        else:
            self.file_changes = "Local copy was not found"

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
        if self.selected_file is not None:
            ps_file_path = os.path.join(client_files_dir, self.selected_file)

            with open(ps_file_path, "w") as f:
                content = self.get_text()
                content = content.encode('utf-8')
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
        # block text area
        self.text.config(state=DISABLED, background="gray")

    def unblock_text_window(self):
        self.text.config(state=NORMAL, background="white")

    # Delete button block
    def block_delete_button(self):
        self.menu.entryconfigure("Delete file", state="disabled")

    # Delete button release
    def release_delete_button(self):
        self.menu.entryconfigure("Delete file", state="normal")

    # Block and reset Access radio buttons
    def block_access_buttons(self):
        self.public_access.configure(state="disabled")
        self.private_access.configure(state="disabled")

    # Update Access radio buttons
    def choose_access_button(self, file_access):
        # Unfreeze buttons if they're not active
        self.public_access.configure(state="normal")
        self.private_access.configure(state="normal")

        # Select current access to file in radio button
        if file_access == ACCESS.PRIVATE:
            self.private_access.select()

        elif file_access == ACCESS.PUBLIC:
            self.public_access.select()

    # (un)Block the button "check changes"
    def block_button_check_changes(self):
        self.button_check_changes.config(state=DISABLED)

    def unblock_button_check_changes(self):
        self.button_check_changes.config(state=NORMAL)

    def set_notification_status(self, message, err_code=None):
        if err_code:
            message += ".\n" + error_code_to_string(err_code)

        self.status.set("Last action: " + message)


    # NOTIFICATION UPDATES (From server) ===============================================================
    # ======== Some change was made in file by another client ==========================================
    def notification_update_file(self, change):
        '''
        Another client made the change => update text window
        :param change: (string) in format
        '''

        # Parse change that arrived from server
        # position is in format "row.column"
        file_to_change, change_type, pos, key = parse_change(change, case_update_file=True)

        # And check whether the selected file matches with file in change
        if self.selected_file and self.selected_file == file_to_change:
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

    # ======== Another client created a document with public access ====================================
    def notification_file_creation(self, change):
        file_name = parse_change(change)
        file_name = file_name[0]

        # Update file list
        self.files_list.insert(END, file_name)

        # Update notification bar
        self.set_notification_status("another client created file with public access")

    # ======== Another client deleted a document =======================================================
    def notification_file_deletion(self, change):
        '''
        :param change: (string) contain file
        '''
        deleted_file = parse_change(change)
        deleted_file = deleted_file[0]

        # Delete file from menu and its local copy and block the window if current=changed_file
        notification = "owner deleted file " + str(deleted_file)
        self.remove_file_from_menu_and_delete_local_copy(deleted_file, notification)

    # ======== Another client changed the access to the file (made it private/public) ==================
    def notification_changed_access_to_file(self, change):
        file_name, access = parse_change(change)

        # Owner changed access to file to Private status
        if access == ACCESS.PRIVATE:
            notification = "another client changed access file " + str(file_name) + " to private"
            notification += ". Local copy deleted"

            # Delete file from menu and its local copy and block the window if current=changed_file
            self.remove_file_from_menu_and_delete_local_copy(file_name, notification)

            # Freeze some buttons (access/delete/text)
            self.set_state_after_deletion()

        # Owner changed access to file to Public status
        elif access == ACCESS.PUBLIC:
            # Add file to the end of list of files
            self.files_list.insert(END, file_name)

            notification = "another client opened access to file " + str(file_name)
            self.set_notification_status(notification)


    # OTHER FUNCTIONS ==================================================================================
    # Reset states after deletion
    def set_state_after_deletion(self):
        self.clear_text()
        self.block_delete_button()
        self.block_access_buttons()
        self.block_text_window()
        self.selected_file = None
        self.block_button_check_changes()

    # Delete file from menu and its local copy (if exists)
    def remove_file_from_menu_and_delete_local_copy(self, file_name, notification=None):
        '''
        :param file_name: (string) file that should ne deleted
        :param notification: (string)
            optional param. Will update status bar, if the deletion was performed
        :return: (Boolean) True if file deletion was performed
        '''
        wasFileRemoved = False

        files_in_menu = self.files_list.get(0, END)

        if file_name in files_in_menu:
            for index, file_in_menu in enumerate(files_in_menu):
                if file_name == file_in_menu:
                    # Delete file from menu
                    self.files_list.delete(index)

                    # Update status bar
                    if notification:
                        self.set_notification_status(notification)

                    wasFileRemoved = True
                    break

        # Delete local copy of the file
        self.client.delete_local_file_copy(file_name)

        # Check if deleted file is currently opened in the text window
        if self.selected_file and self.selected_file == file_name:
            # Change states for some buttons (as after deletion)
            self.set_state_after_deletion()

            # Set prev. selected file to None to avoid conflicts (when user presses on keys)
            self.selected_file = None

        return wasFileRemoved
