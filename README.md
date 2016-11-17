# Online editor 0.0.1
## Done:
* Basic functions: send/receive
* server generates user_id and send it back to the clien (if neccessary)
* notifying the server about existing user_id
* client stores user_id in the file config.ini
* list of accessible files (client-server-client)
* delete a file on server and local copy on client
* created a config file on the server and its structure (LIMITED_FILES, OWNERS_FILES)

## TODO Client:
* ??? send to all clients (except the user user thread) a latest copy of file (if user's changed something) (client should not notify other clients, it should notify only server about changes)
* ??? send a new opened file (what do you mean?)
* request to create a new file on the server


## TODO Server:
* store all edited docs in the app folder (to compare mismatches in future) (instead of app folder we can use sql DB)
* if client changes the doc, send request to server to notify other connected users
* when user connected to server, server compares local user's file to the last file's version stored in server and renews user's file if needed
* notify clients when the file was deleted ( we can remove files without notification)
* save owner of the file to the config(format: file_name = owner_id, section: OWNERS_FILES)

## TODO GUI:
* update file list when the file was deleted
* show list of accessible files
* action to create a new file
* action to delete a file
* find how to recognize that user pushed "delete" button?
