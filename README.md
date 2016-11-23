# Online editor 0.0.3
## Done:
* Basic functions: send/receive
* server generates user_id and send it back to the clien (if neccessary)
* notifying the server about existing user_id
* client stores user_id in the file config.ini
* list of accessible files (client-server-client)
* delete a file on server and local copy on client
* created a config file on the server and its structure (LIMITED_FILES, OWNERS_FILES)
* save owner of the file to the server config(format: file_name = owner_id, section: OWNERS_FILES)
* send request to create a new file on the server (client)
* server wants to close all the connections (break while)
* fixed a bug with reading config to get the freshest data
* show list of accessible files (GUI)
* added comparison of local file (if exist) and original content on the server (GUI file, client side)
* store all docs in the file folder (personal for client, and personal for server)
* connect msg box with file name and checkbox to this function (GUI)
* send the request to the server with last change in the file (can be delete/insert/enter/backspace operation) (client side)
* if client requested to update the doc. Save the changes on the server (server)
* find how to recognize that user pushed "delete" key (GUI)
* action to create a new file (GUI)
* create asynchronous receiving to receive notification about file updating (in process) (Client)
* send request to other clients last change in the file (queue that collect changes has name "changes")


* update file list when the file was created (request from the server that new file is accessible) (GUI)
* update file list when the file was deleted (GUI)
* create and handle action to delete a file (GUI/Client/Server)
* Block text area, radio buttons reset selection, and freeze delete button (as well as notification about deletion arrived and deleted file was opened at that moment)
* After file deletion, it also will be removed from menu
* File can be deleted only by owner
* Change access to the file (gui/client/server)
* When user changed access to Private, other clients will be rechecked and if they have this file in menu, then local copy will be deleted and the item in menu as well
* When user changed access to Public, then other clients will receive msg to add item to the list of files menu
* notify clients if the file was created with a public access (GUI/client/server)
* notify clients if the file was deleted (GUI/client/server)
* create a window (by click on check changes) to show the changes between local copy of file and file on server (GUI)
* write and show changes between local copy and download file

## TODO Client/Server/GUI:
* !!! Problem with typing ASKII symbols


## !!! Do not do:
* user deletes selected region of text

![View of our online editor](http://clip2net.com/clip/m527982/98895-clip-176kb.png)
