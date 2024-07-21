import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
import asyncio
import websockets
import os
import json
import base64
import rsa
import argparse
import threading
import websockets.sync.client

#variable to store the private key
private_key_pem_base64=""

#Function to check if an object passed to it is json or not 
def is_json(temp):
    try:
        json_object = json.loads(temp)
    except ValueError as e:
        return False
    return True

#FUnction to add the message to the User Interface of the Client
def add_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END, message + '\n')
    message_box.config(state=tk.DISABLED)

#Function to update the dropdown list of recipients and groups
def update_dropdown():
    print(options)
    print(options[0])
    selected_option.set(options[0][0]) 
    dropdown['menu'].delete(0, 'end')  
    for option in options:
        dropdown['menu'].add_command(label=option[0], command=tk._setit(selected_option, option[0]))
    selected_option_width = max(len(option[0]) for option in options) + 2
    dropdown.config(width=selected_option_width)

#Function to send a file to the server when the File button is clicked
#The filename is sent first in json format and the file is sent after. Finally, a message that the user sent the file is displayed in the message textbox.
def send_file():
    file_addr = filedialog.askopenfilename()
    recp=selected_option.get()
    if file_addr:
        try:
            file_name = os.path.basename(file_addr)
            message="FILE~"+file_name
            data={
            "msg": message,
            "recipient": recp 
            }
            json_data = json.dumps(data)
            client.send(json_data.encode())
            with open(file_addr, "rb") as file:
                abcd=file.read()
                client.send(abcd)
            username = username_textbox.get()
            messageclient = username + " sent file: " + file_name
            add_message(messageclient)
        except Exception as e:
            messagebox.showerror("File Transfer Error", str(e))

# This function is used to send a message from client to other clients. Based on the client, rsa encryption is performed here
# and the message is sent as json object.
def send_message():
    message = message_textbox.get()
    recp=selected_option.get()
    if message != '':
        if recp!="all" and "(g)" not in recp:
            for option in options:
                if option[0] == recp:
                    pem=base64.b64decode(option[1])
                    recipientspublickey = rsa.PublicKey.load_pkcs1(pem)
                    message = rsa.encrypt(message.encode('utf-8'), recipientspublickey)
            message=base64.b64encode(message).decode('utf-8')
        data={
            "msg": message,
            "recipient": recp 
        }
        json_data = json.dumps(data)
        client.send(json_data.encode())
        message_textbox.delete(0, len(message))
    else:
        messagebox.showerror("Empty message", "Message cannot be empty")

# This function is to send a request to server to join a group which has already been created.
def join_group():
    message = group_join_textbox.get()
    if message != '':
        if "(g)" in message:
            output=message
        else:
            output=message+"(g)"
        data={
            "msg": output,
            "recipient": "joingroup" 
        }
        json_data = json.dumps(data)
        client.send(json_data.encode())
        group_join_textbox.delete(0, len(message))
        
    else:
        group_join_textbox.showerror("Empty message", "Group Name is empty")


#This function is used to create a group by sending a request to server for group creation
def create_group():
    message = group_creation_textbox.get()
    if message != '':
        data={
            "msg": message+"(g)",
            "recipient": "creategroup" 
        }
        json_data = json.dumps(data)
        client.send(json_data.encode())
        group_creation_textbox.delete(0, len(message))

    else:
        messagebox.showerror("Empty message", "Group Name be empty")


#This is one of the core functions of the client code. This listens for any communication from the server and handles it based on several factors.
#If its a json object that is returned it checks if the server sent the username list, private key, s2s message, group message or joining message or a file.
#If its a message, then RSA decryption is applied before loading the data in the message box of the User Interface.
def listen(client):

    while True:
        message_raw = client.recv()
        if message_raw != '':
            print(message_raw)
            if is_json(message_raw):
                decoded=json.loads(message_raw)
                type=decoded.get("type")
                if type=="private_key":
                    global private_key_pem_base64
                    private_key_pem_base64=decoded.get("msg")
                elif type=="username_list":
                    global options 
                    options = [("all",None)] + decoded.get("msg")
                    print(options)
                    update_dropdown()
                elif type=="all" or type=="joiningmsg":
                    username = decoded.get("msg").split(":")[0]
                    content = decoded.get("msg").split(':')[1]
                    print(username,content)
                    add_message(f"[{username}] {content}")
                elif type=="file":
                    filename= decoded.get("msg").split("~")[1]
                    print("Received from Server",filename)
                    with open(filename, "wb") as file:
                        while True:
                            chunk = client.recv()
                            if chunk == b"EOF":
                                break
                            file.write(chunk)
                    add_message(filename + " Received")
                elif type=="message":
                    recp=decoded.get("recipient")
                    username=decoded.get("sent")
                    content=decoded.get("msg")
                    content=base64.b64decode(content.encode('utf-8'))
                    pem=base64.b64decode(private_key_pem_base64)
                    myprivatekey = rsa.PrivateKey.load_pkcs1(pem)
                    message = rsa.decrypt(content, myprivatekey)
                    content=message.decode('utf-8')
                    print(username,content)
                    add_message(f"[{username}] {content}")
                elif type=="group":
                    username = decoded.get("msg").split(":")[0]
                    content = decoded.get("msg").split(':')[1]
                    print(username,content)
                    add_message(f"[{username}] {content}")

            else:
                username = message_raw.split(":")[0]
                content = message_raw.split(':')[1]
                content=base64.b64decode(content.encode('utf-8'))
                pem=base64.b64decode(private_key_pem_base64)
                myprivatekey = rsa.PrivateKey.load_pkcs1(pem)
                message = rsa.decrypt(content, myprivatekey)
                content=message.decode('utf-8')
                print(username,content)
                add_message(f"[{username}] {content}")

        else:
            messagebox.showerror("Error", "Message recevied from server is empty")

#This function is used to connect to the websocket server based on the port(default or specified). 
# It then sends the username from the client interface to the server, which the server uses to create a new user.
# The server creates the RSA public and private key pair, then returns the private key to the user which is stored in private_key_pem_base64.
# THe username list is also updated here.
def connect():
    parser = argparse.ArgumentParser(description="Python Chat Client")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server IP')
    parser.add_argument('--port', type=int, default=8080, help='Port')
    args = parser.parse_args()

    host = args.host
    port = args.port
    global client
    try:
        global client
        final_host="ws://"+str(host)+":"+str(port)
        client = websockets.sync.client.connect(final_host)
        print("Successfully connected to server")
        add_message("[SERVER] Successfully connected to the server")
    except:
        errormsg="Unable to connect to server" + str(host) + ":"+str(port)
        messagebox.showerror("Unable to connect to server", errormsg)
    username = username_textbox.get()
    if client and username != '':
        client.send(username.encode())
        message_raw=client.recv()
        decoded=json.loads(message_raw)
        type=decoded.get("type")
        if type=="private_key":
            global private_key_pem_base64
            private_key_pem_base64=decoded.get("msg")
        else:
            global options 
            options = [("all",None)] + decoded.get("msg")
            print(options)
            update_dropdown()
    else:
        messagebox.showerror("Invalid username", "Username cannot be empty")
    if(client):
        username_textbox.config(state=tk.DISABLED)
        username_button.config(state=tk.DISABLED)
        threading.Thread(target=listen, args=(client, )).start()
    else:
        pass

#THe following defines the UI for the application. You need to understand the tkinter syntax to understand the following code.
root = tk.Tk()
root.geometry("600x700") # uses width by height
root.title("Messenger Client")
root.resizable(False, False)

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=2)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=1)

top_frame = tk.Frame(root, width=600, height=100, bg="#475569")
top_frame.grid(row=0, column=0, sticky=tk.NSEW)

middle_frame = tk.Frame(root, width=600, height=200, bg="#E2E8F0")
middle_frame.grid(row=1, column=0, sticky=tk.NSEW)

bottom_frame = tk.Frame(root, width=600, height=100, bg="#475569")
bottom_frame.grid(row=2, column=0, sticky=tk.NSEW)

dropdown_frame = tk.Frame(root, width=600, height=100, bg="#0284C7")
dropdown_frame.grid(row=3, column=0, sticky=tk.NSEW)

creategroup_frame = tk.Frame(root, width=600, height=100, bg="#475569")
creategroup_frame.grid(row=4, column=0, sticky=tk.NSEW)

joingroup_frame = tk.Frame(root, width=600, height=100, bg="#475569")
joingroup_frame.grid(row=5, column=0, sticky=tk.NSEW)

username_label = tk.Label(top_frame, text="Enter username:", font=("Helvetica", 17), bg="#475569", fg="white")
username_label.pack(side=tk.LEFT, padx=10)

username_textbox = tk.Entry(top_frame, font=("Helvetica", 17), bg="#E2E8F0", fg="black", width=23)
username_textbox.pack(side=tk.LEFT)

username_button = tk.Button(top_frame, text="Join", font=("Helvetica", 15), bg="#0284C7", fg="white", command=connect)
username_button.pack(side=tk.LEFT, padx=15)

message_textbox = tk.Entry(bottom_frame, font=("Helvetica", 17), bg="#E2E8F0", fg="black", width=32)
message_textbox.pack(side=tk.LEFT, padx=10)


message_button = tk.Button(bottom_frame, text="Send", font=("Helvetica", 13), bg="#0284C7", fg="white", command=send_message)
message_button.pack(side=tk.LEFT, padx=10)

file_button = tk.Button(bottom_frame, text="File",font=("Helvetica", 13), bg="#0284C7", fg="white",  command=send_file)
file_button.pack(side=tk.LEFT, padx=10)

message_box = scrolledtext.ScrolledText(middle_frame, font=("Helvetica", 12), bg="#E2E8F0", fg="black", width=67, height=26.5)
message_box.config(state=tk.DISABLED)
message_box.pack(side=tk.TOP)

groupcreate_label = tk.Label(creategroup_frame, text="Enter name of group:", font=("Helvetica", 12), bg="#475569", fg="white")
groupcreate_label.pack(side=tk.LEFT, padx=10)

group_creation_textbox = tk.Entry(creategroup_frame, font=("Helvetica", 12), bg="#E2E8F0", fg="black", width=21)
group_creation_textbox.pack(side=tk.LEFT, padx=10)

group_creation_button = tk.Button(creategroup_frame, text="Create Group", font=("Helvetica", 12), bg="#0284C7", fg="white", command=create_group)
group_creation_button.pack(side=tk.LEFT, padx=10)

groupjoin_label = tk.Label(joingroup_frame, text="Enter name of group:", font=("Helvetica", 12), bg="#475569", fg="white")
groupjoin_label.pack(side=tk.LEFT, padx=10)

group_join_textbox = tk.Entry(joingroup_frame, font=("Helvetica", 12), bg="#E2E8F0", fg="black", width=21)
group_join_textbox.pack(side=tk.LEFT, padx=10)

group_join_button = tk.Button(joingroup_frame, text="Join Group", font=("Helvetica", 12), bg="#0284C7", fg="white", command=join_group)
group_join_button.pack(side=tk.LEFT, padx=10)


options = [("all", None)]
selected_option = tk.StringVar()
selected_option.set(options[0])
selected_option_width = max(len(option) for option in options) + 2


recipient = tk.Label(dropdown_frame, text="Select the Recipient", font=("Helvetica", 12), bg="#475569", fg="white")
recipient.pack(side=tk.LEFT, padx=10)

dropdown = ttk.OptionMenu(dropdown_frame, selected_option, *options)
dropdown.config(width=selected_option_width)
dropdown.pack(pady=10)


def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def main():
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_event_loop, args=(loop,), daemon=True).start()
    root.mainloop()
    
if __name__ == '__main__':
    main()