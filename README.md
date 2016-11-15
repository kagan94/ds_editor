# Online editor 0.0.1
## Done:
* Basic functions: send/receive
* server generates user_id and send it back to the clien (if neccessary)
* notifying the server about existing user_id
* client stores user_id in the file config.ini

## TODO Client:
* send to all clients (except the user user thread) a latest copy of file (if user's changed something)
* send a new opened file
* request to create a new file on the server
* update list of accessible files
* delete file request (as well local copy of the file, if the result of requst was successful)

## TODO Server:
* store all edited docs in the app folder (to compare mismatches in future)
* if client changes the doc, send request to server to notify other users
* send the list of accessible files
* get request to delete a file

## GUI TODO:
* show list of accessible files
* action to create a new file
* action to delete a file
* find how to recognize that user pushed "delete" button?
