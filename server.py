import socket
import time
import threading
import random

ip_pool=[
    "192.168.1.10","192.168.1.11","192.168.1.12","192.168.1.13","192.168.1.14",
    "192.168.1.15","192.168.1.16","192.168.1.17","192.168.1.18","192.168.1.19",
    "192.168.1.20"
]

assigned={}
past_leases={}
lease_duration=10

server_ip="0.0.0.0"
port=1010

def lease_cleaner():
    while True:
        now=time.time()
        expired=[cid for cid,(ip,end) in assigned.items() if now>end]
        for cid in expired:
            ip,_=assigned.pop(cid)
            ip_pool.append(ip)
            print(f"[LEASE EXPIRED] {cid} → {ip} returned to pool")
        time.sleep(1)

threading.Thread(target=lease_cleaner,daemon=True).start()

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((server_ip,port))
s.listen(5)

print("\nDHCP SERVER RUNNING:")
print(f"Lease time: {lease_duration} seconds\n")

def select_ip_for(client_id):
    if client_id in past_leases:
        old=past_leases[client_id]
        if old in ip_pool:
            return old
    if ip_pool:
        return random.choice(ip_pool)
    return None

while True:
    conn,addr=s.accept()
    data=conn.recv(1024).decode().strip()
    if not data:
        conn.close()
        continue

    client_id=addr[0]
    print(f"Client {addr} → {data}")

    if data=="DISCOVER":
        offer_ip=select_ip_for(client_id)
        if offer_ip:
            conn.send(f"OFFER {offer_ip}".encode())
            print(f"[OFFER] {client_id} ← {offer_ip}")
        else:
            conn.send("NO_IP_AVAILABLE".encode())

    elif data.startswith("REQUEST"):
        _,req_ip=data.split()
        if req_ip not in ip_pool:
            conn.send("NACK".encode())
            print(f"[NACK] {client_id} requested invalid IP {req_ip}")
        else:
            assigned[client_id]=(req_ip,time.time()+lease_duration)
            past_leases[client_id]=req_ip
            ip_pool.remove(req_ip)
            conn.send(f"ACK {req_ip}".encode())
            print(f"[ACK] {client_id} assigned {req_ip}")

    elif data=="RELEASE":
        if client_id in assigned:
            ip,_=assigned.pop(client_id)
            ip_pool.append(ip)
            conn.send(f"RELEASED {ip}".encode())
            print(f"[RELEASE] {client_id} returned {ip}")
        else:
            conn.send("NOT_FOUND".encode())

    conn.close()

    print("\nCURRENT ASSIGNMENTS:\n")
    if assigned:
        for cid,(ip,end) in assigned.items():
            print(f"{cid:15} → {ip} | {int(end-time.time())}s left")
    else:
        print("No active leases")
    print()
