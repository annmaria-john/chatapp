# CHATAPP

### This project is a real-time chat application built using Python and the WebSocket protocol. The application features a graphical user interface (GUI) created with Tkinter and aims to provide a platform for studying protocol design, security, and vulnerabilities. The application intentionally includes backdoors to understand and exploit vulnerabilities.

##### Github URL : https://github.com/annmaria-john/chatapp.git 


#### Compilation
1.	Install python3 on your local machine.
2.	Download the zip file and extract the chat app folder. There should be two folders – client and server.
3.	Inside the two folders there is the client and server python code. For each python code you need to install the following dependencies using “pip install” - 
-	rsa
-	websockets
-	asyncio
-	tkinter
4.	Open the terminal and change to client directory to run the client code – 
python clientcode_web.py
5.	Open the terminal and change to server directory to run the server code – 
python servercode_web.py
6.	This opens up the server on the port 8080 and the client will connect to this default port unless an argument is specified.

#### Configuration
1.	Client to server(only)
*	Run the server code with the following optional parameters
python servercode_web.py –host <IP Address> --port <port number>
*	The host parameter is the IP address of your server and the port number is the port where the server listens.
*	Run the client code with the following optional parameters
python clientcode_web.py --host <IP Address> --port <port number>
*	The host parameter is the IP address of your client and the port number is the port where the client connects.
2.	Client to server to server to client
*	Run the server code with the following required parameters
python servercode_web.py. 
*	This opens up our first server on port 8080(for client connections) and port 5050(for server to server connections)
*	Run the server code with the following required parameters
python servercode_web.py --port 2020 --serverport 5051
*	This opens up our second server on port 2020(for client connections) and port 5051(for server to server connections)
*	Run the client code 
python clientcode_web.py 
*	The first client by default connects to the port 8080
*	Run the client code with the following required parameters
python clientcode_web.py --port 2020 
*	This opens up the second client which connects to the port 2020

#### Assumptions
1.	Server to Server communication can handle only 1-1 messages and 1-all messages(no file sharing and group messaging)
2.	You can only transfer files for 1-1 client communication, not group communication
3.	For server to server communication, the two servers have to serve their s2s connection on port 5050 and 5051.

#### Working - client to server
![image](https://github.com/user-attachments/assets/cb26ec1e-f11e-48ea-a2d1-ba08e34f6146)
The clients join the chatapp by logging in with a username.
 ![image](https://github.com/user-attachments/assets/220db569-c270-42d4-b6c1-0a9ac6152c08)

Client 1(Alice) can send a message by writing it in the text box.
 ![image](https://github.com/user-attachments/assets/b4b8df47-ced4-4937-ab9f-bf39206d82b7)

Alice has created a group - math
 ![image](https://github.com/user-attachments/assets/07211751-7e9a-4e04-b5b3-0ce5946ea5e6)

The group is visible to all clients in the drop down menu. (g) against the username indicates the group.
![image](https://github.com/user-attachments/assets/237e32e8-57c5-4b92-9881-50624fbbfdb8)
 
Client harry has joined the group math and Alice has messaged the group 
![image](https://github.com/user-attachments/assets/ad83994d-9398-4d16-a13a-8c32cae261b2)

Alice has sent a text file file1.txt to bob
![image](https://github.com/user-attachments/assets/39e2cdd1-2910-444b-8e41-0304f26e7b9c)

#### Working – server to server
![image](https://github.com/user-attachments/assets/48f93b92-798a-4ab6-8849-0ba3c1957b48)

Becky has joined from server 1 and Zach has joined server 2.
Becky has send a message to Zach by selecting him from the drop down in the recipients.
![image](https://github.com/user-attachments/assets/13af3969-62ef-461a-9d24-6afa1f136d90)

Zach has sent a message to all recipients
![image](https://github.com/user-attachments/assets/a913adc8-f28f-40bd-a165-6bfae018b75b)

 






