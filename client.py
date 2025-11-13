import socket
import time

server_ip = "192.168.56.1"

port = 9999

client_name = input("Enter client name: ")

# DISCOVER
s = socket.socket()
s.connect((server_ip, port))
s.send("DISCOVER".encode())
msg = s.recv(1024).decode()
s.close()

if msg.startswith("OFFER"):
    offered_ip = msg.split()[1]
    print(f"[DISCOVER] Server offered: {offered_ip}")

    # REQUEST
    time.sleep(1)
    s = socket.socket()
    s.connect((server_ip, port))
    req = f"REQUEST {client_name} {offered_ip}"
    s.send(req.encode())
    msg2 = s.recv(1024).decode()
    s.close()

    if msg2.startswith("ACK"):
        print(f"[REQUEST] ACK received. IP assigned: {offered_ip}")
        print("Client now using this IP...\n")

        # simulate using IP (lease can expire automatically)
        print(f"Using IP for 15 seconds...")
        time.sleep(15)

        # RELEASE manually (optional)
        s = socket.socket()
        s.connect((server_ip, port))
        rel = f"RELEASE {client_name}"
        s.send(rel.encode())
        msg3 = s.recv(1024).decode()
        s.close()
        print(f"[RELEASE] {msg3}")
    else:
        print("Request denied or failed.")

else:
    print("No IP available from server.")
