# Online editor 0.0.1
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

## TODO Client:
* send the request to the server with changes in the file
* create asynchronous receiving to receive notification about file updating

## TODO Server:
* store all edited docs in the app folder (to compare mismatches in future)
* if client requested update the doc. Save the changes on the server and send request to other clients to update version of file
* when user connected to server, server compares local user's file to the last file's version stored in server and renews user's file if needed
* notify clients if the file was deleted
* notify clients if the file was created with a public access
* FIX Bug with reading config to get the freshest data


## TODO GUI:
* update file list when the file was deleted
* show list of accessible files
* action to create a new file
* action to delete a file
* find how to recognize that user pushed "delete" key?
