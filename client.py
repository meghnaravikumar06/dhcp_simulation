import socket
import time
import uuid

server_port = 6767
lease_time = 0
assigned_ip = None
mac = str(uuid.uuid4())[:12]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(3)

broadcast_addr = ("255.255.255.255", server_port)

sock.sendto(f"DISCOVER {mac}".encode(), broadcast_addr)
data, server = sock.recvfrom(1024)
_, offer_ip = data.decode().split()
print(f"[OFFER] {offer_ip}")

sock.sendto(f"REQUEST {mac} {offer_ip}".encode(), server)
data, server = sock.recvfrom(1024)
_, assigned_ip, lease_time = data.decode().split()
lease_time = int(lease_time)
print(f"[ACK] {assigned_ip} lease={lease_time}")

MAX_RENEWS = 2
renew_count = 0

start = time.time()

while True:
    time.sleep(lease_time // 2)

    if renew_count >= MAX_RENEWS:
        print("Renew limit reached. Allowing lease to expire.")
        break

    sock.sendto(f"RENEW {mac}".encode(), server)
    data, server = sock.recvfrom(1024)
    _, assigned_ip, lease_time = data.decode().split()
    lease_time = int(lease_time)
    renew_count += 1
    print(f"[RENEW] {assigned_ip} ({renew_count}/{MAX_RENEWS})")

print("Client stopping renewals. Waiting for server to expire lease.")

while True:
    time.sleep(1)
