import socket
import time

server_ip="10.238.46.148"
port=1010

try:
    s=socket.socket()
    s.connect((server_ip,port))
    s.send("DISCOVER".encode())
    msg=s.recv(1024).decode()
    s.close()
except:
    print("Could not reach DHCP server.")
    exit()

if not msg.startswith("OFFER"):
    print("No IP available from server.")
    exit()

offered_ip=msg.split()[1]
print(f"[DISCOVER] Server offered IP: {offered_ip}")

time.sleep(1)

s=socket.socket()
s.connect((server_ip,port))
s.send(f"REQUEST {offered_ip}".encode())
msg2=s.recv(1024).decode()
s.close()

if msg2.startswith("ACK"):
    print(f"[REQUEST] ACK received → Lease granted for {offered_ip}")
    time.sleep(5)

    s=socket.socket()
    s.connect((server_ip,port))
    s.send("RELEASE".encode())
    msg3=s.recv(1024).decode()
    s.close()
    print(f"[RELEASE] {msg3}")

elif msg2.startswith("NACK"):
    print("[REQUEST] Server rejected the IP request.")
else:
    print("Unexpected server response.")
