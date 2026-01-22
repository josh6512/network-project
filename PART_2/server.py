import socket
import threading

# Server Configuration
host = '127.0.0.1'
port = 1234
clients_dict = {} 

ServerSocket = socket.socket()
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ServerSocket.bind((host, port))
ServerSocket.listen(5)

def threaded_client(connection):
    # Registration Phase: Receive unique nickname
    connection.send(str.encode('SERVER: Enter your unique nickname: '))
    try:
        name = connection.recv(1024).decode('utf-8').strip()
    except:
        connection.close()
        return
    
    # Check if name is already taken
    if name in clients_dict:
        connection.send(str.encode('SERVER: Name already taken. Closing connection.'))
        connection.close()
        return

    clients_dict[name] = connection
    print(f"User {name} is now online.")
    connection.send(str.encode(f"Welcome {name}! To chat, type: target_name:message\n"))

    while True:
        try:
            data = connection.recv(2048).decode('utf-8')
            if not data:
                break
            
            # Message Analysis: We expect format "target_name:message"
            if ":" in data:
                target_name, message = data.split(":", 1)
                target_name = target_name.strip()
                
                if target_name in clients_dict:
                    # Find target client socket and forward the message
                    target_socket = clients_dict[target_name]
                    forward_msg = f"Message from {name}: {message}"
                    target_socket.send(str.encode(forward_msg))
                else:
                    connection.send(str.encode(f"SERVER: User {target_name} not found."))
            else:
                # If the user didn't use the format name:message
                connection.send(str.encode("SERVER: Invalid format. Use 'name:message'"))
                
        except Exception as e:
            print(f"Error: {e}")
            break

    # Cleanup on disconnection
    print(f"User {name} disconnected.")
    if name in clients_dict:
        del clients_dict[name]
    connection.close()

print("Server is waiting for clients...")
while True:
    Client, address = ServerSocket.accept()
    print(f"Connected to: {address[0]}:{address[1]}")
    t = threading.Thread(target=threaded_client, args=(Client,))
    t.daemon = True
    t.start()