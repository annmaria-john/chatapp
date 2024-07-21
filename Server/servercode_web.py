import asyncio
import websockets
import json
import base64
import rsa
import time
import argparse
import sys
import websockets.sync.client

t=0
server_usernames=[]
server_users={}
all_clients = [] # An array of tuple (username, client socket object)
groups={} # A dictionary of groupname(key) and groupmembers(value - array)
usernames= [] # An array of tuple of usernames and their public keys
serv_usernames=[]
ports = [5050, 5051]

#Function to check if an object passed to it is json or not 
def is_json(temp):
    try:
        json_object = json.loads(temp)
    except ValueError as e:
        return False
    return True

#Function to establish server to server communication 
async def send_to_servers(msg):
    tasks = []
    for server in ports:
        if(server!=server_port):
            tasks.append(send_to_server(server, msg))
    await asyncio.gather(*tasks)

#Function which establishes the s2s connection, and retries the connection every 5 seconds
async def send_to_server(server, msg):
    global t
    uri = "ws://"+server_host+":"+str(server)
    while True:
        try:
            global servclient
            servclient = websockets.sync.client.connect(uri) 
            t=1
            servclient.send(msg)
            break
        except (websockets.ConnectionClosedError, ConnectionRefusedError) as e:
            print("Connection to "+ str(server)+ " failed, retrying in 5 seconds...")
            await asyncio.sleep(5)

#Function to send a message from server 1 to server 2 or vice versa
async def send_to_server2(msg):
            if t==0:
             return
            print("I am in send2server2")
            if not servclient:
                print("Server client socket is not defined, retrying in 5 seconds...")
                return
            try:
                servclient.send(msg)
            except (websockets.ConnectionClosedError, ConnectionRefusedError) as e:
                print("Connection to "+ servclient + "failed, retrying in 5 seconds...")
                print("Failed to send - From send to server2!!!!")

#This function sends a message from the server to the client. The message is sent in different ways based on whether its a json object, a file or just a message.                
async def send_message(client, msg):
    if is_json(msg):
        msg1=json.loads(msg)
        type=msg1.get("type")
        if type=="file":
            filename=msg1.get("msg").split("~")[1]
            await client.send(msg)
            time.sleep(1)
            with open(filename, "rb") as file:
                while chunk := file.read(1024):
                    await client.send(chunk)
                await client.send(b"EOF") 
            print(f"File sent from server")
        else:
            print("sending message",msg)
            await client.send(msg)
    else:
        print("sending message",msg)
        await client.send(msg)

#This function is used to send to a recipient and does checks wether the recipient is a group or is to be sent to all the users or a specific recipient.
async def send_messages(msg,recp,username):
    if recp in groups:
        print("The Recipient is a group: Sending message to all group members")
        json_ob=json.dumps({"msg":recp+msg,"type":"group"})
        if username in groups[recp]:
            for each_user in groups[recp]:
                for client in all_clients:
                    if each_user == client[0]:
                        await send_message(client[1], json_ob)
        else:
            print("Username ", username, " is not in ", groups[recp])
    else:
        if recp == "all":
            json_obj=json.dumps({
                 "msg": msg,
                 "type": "all"
             }) 
            for client in all_clients:
                await send_message(client[1],json_obj)
        else:
            for client in all_clients:
                if recp == client[0]:
                    await send_message(client[1], msg)
                    break
                else:
                    print("Recipient not found")


# This function is used to receive a file from the client and forward it to the intended recipient.
async def receive_file(client, file_name, recipient,username):
    with open(file_name, "wb") as file:
        chunk = await client.recv()
        file.write(chunk)
    msgtmp="SERVER: Received file " + file_name
    json_obj=json.dumps({
        "msg":msgtmp,
        "type": "joiningmsg"
    })
    await send_message(client,json_obj)
    msgtemp="FILE~"+file_name
    msg=json.dumps({
                "msg": msgtemp,
                "type": "file"
            })
    await send_messages(msg,recipient,username)

# This function listens for any message from the client. It loads the json object and 
# then checks for the type of request(create group, join group, send message using s2s, send group messages to everyone and receive files) 
async def listen(client, username):

        try:
            async for msgrecv in client:
                print(usernames)
                data = json.loads(msgrecv)
                msg = data.get('msg')
                recipient=data.get('recipient')
                flag=0
                if msg != '':
                    for user in serv_usernames:
                     if recipient==user[0]:
                            flag=1
                            final_msg=json.dumps({
                                "recipient": recipient,
                                "sent":username,
                                "msg": msg,
                                "type":"message"
                            })
                            await send_to_server2(final_msg)
                    if flag==1:
                        continue
                    elif recipient=="creategroup":
                        groups[msg]=[username]
                        usernames.append((msg,None))
                        print(groups)
                        username_list=json.dumps({"msg":usernames+serv_usernames,
                                                  "type":"username_list"})
                        server_userslist=json.dumps({
                        "type":"presence",
                        "presence":usernames,
                        "port":server_port
                            })
                        for client in all_clients:
                            await client[1].send(username_list)
                        await send_to_server2(server_userslist)
                    elif recipient=="joingroup":
                        if msg in groups:
                            groups[msg].append(username)
                            print(groups)
                    elif recipient == "all":
                        json_obj=json.dumps({
                                "recipient": recipient,
                                "sent":username,
                                "msg": msg,
                                "type":"all"
                            })
                        await send_to_server2(json_obj)
                        output=username+":"+msg
                        await send_messages(output,recipient,username)
                    else:
                        if msg.startswith("FILE~"):
                            file_name = msg.split("~")[1]
                            print("I am here")
                            time.sleep(1)
                            await receive_file(client, file_name, recipient,username)
                        else:
                            output = username + ':' + msg
                            await send_messages(output,recipient,username)
                else:
                    print("The message send from client ", username, " is empty")
        except ConnectionResetError:
            print("Connection Reset Error")

        except Exception as e: 
            print("Error in received object ", e )
            print("Type is", type(e))

# This function listens for any message from the other server. It loads the json object and 
# then checks for the type of request and forwards the message to client based on the type of request 
async def server_listen(server_client, port):

        try:
            print("Inside server listen")
            async for msgrecv in server_client:
                print("Inside server listen async for")
                data = json.loads(msgrecv)
                type = data.get('type')
                global serv_usernames
                if type == 'presence':
                    presence=data.get('presence')
                    port=data.get('port')
                    global server_usernames
                    server_usernames.append((port,server_client))
                    print(server_usernames,presence,port,type)
                    global usernames
                    for i in presence:
                        usern=i[0]
                        serv=i[1]
                        t=0
                        for j in serv_usernames:
                            if j[0]==usern:
                                t=1
                        if t==0 and "(g)" not in usern:
                            serv_usernames.append((usern,serv))
                    username_list=json.dumps({
                        "msg":usernames+serv_usernames,
                        "type": "username_list"
                        })
                    print("sending user list" )
                    for users in all_clients:
                        await users[1].send(username_list)
                elif type=="message":
                    recipient=data.get('recipient')
                    msg=data.get('msg')
                    sent=data.get('sent')
                    if msg.startswith("FILE~"):
                            file_name = msg.split("~")[1]
                            time.sleep(1)
                            with open(file_name, "wb") as file:
                                chunk = await server_client.recv()
                                file.write(chunk)
                            print(port,"server received file")
                            msgtemp="FILE~"+file_name
                            msg=json.dumps({
                                        "msg": msgtemp,
                                        "recipient":recipient,
                                        "type": "file"
                                    })
                            
                            await send_messages(msg,recipient,sent)
                    else:
                            final_msg=json.dumps({
                                "recipient": recipient,
                                "sent":sent,
                                "msg": msg,
                                "type":"message"
                            })
                            await send_messages(final_msg,recipient,sent)
                elif type=="all":
                    recipient=data.get('recipient')
                    msg=data.get('msg')
                    sent=data.get('sent')
                    output=sent+":"+msg
                    await send_messages(output,recipient,sent)
                else:
                    print("The type of message sent from Server client is not defined")
        except ConnectionResetError:
            print("Connection Reset Error")

        except Exception as e: 
            print("Error in received object ", e )
            print("Type is", type(e))


async def s2s_handler(server_client):
    try:
            json_objd = await server_client.recv()
            data = json.loads(json_objd)
            type=data.get('type')
            if type == 'presence':
                presence=data.get('presence')
                port=data.get('port')
                global server_usernames
                server_usernames.append((port,server_client))
                print(server_usernames,presence,port,type)
                global usernames
                global serv_usernames
                global usernames
                for i in presence:
                    usern=i[0]
                    serv=i[1]
                    t=0
                    for j in serv_usernames:
                        if j[0]==usern:
                            t=1
                    if t==0 and "(g)" not in usern:
                        serv_usernames.append((usern,serv))
                username_list=json.dumps({
                    "msg":usernames+serv_usernames,
                    "type": "username_list"
                    })
                print("sending user list" )
                for users in all_clients:
                    await users[1].send(username_list)
                await server_listen(server_client, port)
            
            elif type=="message":
                    recipient=data.get('recipient')
                    msg=data.get('msg')
                    sent=data.get('sent')
                    if msg.startswith("FILE~"):
                            file_name = msg.split("~")[1]
                            time.sleep(1)
                            with open(file_name, "wb") as file:
                                chunk = await server_client.recv()
                                file.write(chunk)
                            print(port,"server received file")
                            msgtemp="FILE~"+file_name
                            msg=json.dumps({
                                        "msg": msgtemp,
                                        "type": "file"
                                    })
                            await send_messages(msg,recipient,sent)
            elif type=="all":
                    recipient=data.get('recipient')
                    msg=data.get('msg')
                    output=sent+":"+msg
                    await send_messages(output,recipient,sent)
            else:
                print("Presence message neither message is not sent!")
    except ConnectionResetError:
        print("Connection Reset Error")

# When the client joins with a username, a public private key pair is generated and the private key is sent back to the user and the public key is sent to everyone.
# The S2S communication The joining message is sent to the clients and the joining message is sent.
async def client_handler(client):
        try:
            global serv_usernames
            print("inside the client handler")
            username = await client.recv()
            username=username.decode('utf-8')
            if username != '':
                (public_key, private_key) = rsa.newkeys(2048)
                public_key_pem = public_key.save_pkcs1(format='PEM')
                public_key_pem_base64=base64.b64encode(public_key_pem).decode('utf-8')
                private_key_pem = private_key.save_pkcs1(format='PEM')
                private_key_pem_base64 = base64.b64encode(private_key_pem).decode('utf-8')
                all_clients.append((username, client))
                usernames.append((username,public_key_pem_base64))
                json_obj=json.dumps({
                    "msg": private_key_pem_base64,
                    "type": "private_key"
                })
                await client.send(json_obj)
                username_list=json.dumps({
                    "msg":usernames+serv_usernames,
                    "type": "username_list"
                    })
                for users in all_clients:
                    await users[1].send(username_list)
                server_userslist=json.dumps({
                        "type":"presence",
                        "presence":usernames,
                        "port":server_port
                    })
                time.sleep(1)
                joiningmsg = "SERVER: "+ username +" joined the chat"
                await send_messages(joiningmsg,"all",username)
                await asyncio.gather( listen(client, username), send_to_servers(server_userslist))
            else:
                print("Client username cannot be empty")
        except ConnectionResetError:
            print("Connection Reset Error")


#The main function gets the arguments to the process and sets it to server the websocket on two ports.

async def main():
    parser = argparse.ArgumentParser(description="Python Chat Server")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host IP')
    parser.add_argument('--port', type=int, default=8080, help='Port')
    parser.add_argument('--serverport', type=int, default=5050, help='Server to Server Port')
    parser.add_argument('--serverhost', type=str, default='127.0.0.1', help='Server to Server Host IP')

    args = parser.parse_args()
    host = args.host
    global server_host
    global server_port
    port = args.port
    server_port = args.serverport
    server_host = args.serverhost
    server = await websockets.serve(client_handler, host, port)
    server2server = await websockets.serve(s2s_handler, host, server_port)
    print(f"Running the server on {host} {port}")
    print(f"Running the server2Server connection on {host} {server_port}")
    await asyncio.gather(
            server.wait_closed(),
            server2server.wait_closed()
        )


if __name__ == '__main__':
    asyncio.run(main())
