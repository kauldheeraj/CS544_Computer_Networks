## Python QUIC Shell

1. Install dependencies with pip (requirements.txt) is provided
2. The certs in the ./certs directory are fine for testing there is a script if you want to rebuild your own but you will need openssl installed
3. run `python3 chat.py server` to start the server with defaults and `python3 chat.py client` to start the client with defaults.
4. User id and passwords that can be used :

| User ID | PassKey |
|---------|-------- |
| deekay  | dheeraj |
| ryan    | reynolds|
| jenny   | jennifer|
| matt    | mathew  |




5. Refer the youtube video for demo :
   https://youtu.be/IhHy6b8g2_0


Correct output for server:

```sh
(.venv) ➜  python git:(main) ✗ python3 chat.py server
[svr] Server starting...
[svr] received message from:  'user name' 
```

Correct output for client:

```sh
(.venv) ➜  python git:(main) ✗ python3 chat.py client
[cli] starting client
[cli] got message from sender:  'user name'
```

```Commands to use on client side prompt:
help
?
login userid password
logoff
send userid simple_text_message         OR
text target_user_id text-message
```Note
To send messages, the userid should be logged in
e.g. send userid some_message