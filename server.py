import socket
import time
import threading
import random

ip_pool=["192.168.1.10","192.168.1.11","192.168.1.12","192.168.1.13","192.168.1.14","192.168.1.15","192.168.1.16","192.168.1.17","192.168.1.18","192.168.1.19","192.168.1.20"]
assigned={}
past_leases={}
lease_duration=10
server_ip="0.0.0.0"
port=1010

def lease_cleaner():
    while True:
        current=time.time()
        expired=[c for c,(ip,end) in assigned.items() if current>end]
        for cname in expired:
            ip,_=assigned.pop(cname)
            ip_pool.append(ip)
            print(f"[LEASE EXPIRED] {cname} → {ip} is back in pool")
        time.sleep(1)

threading.Thread(target=lease_cleaner,daemon=True).start()

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((server_ip,port))
s.listen(5)

print("\nDHCP SERVER RUNNING...")
print(f"Lease time: {lease_duration} seconds\n")

def select_ip_for(cname):
    if cname in past_leases:
        old_ip=past_leases[cname]
        if old_ip in ip_pool:
            return old_ip
    if ip_pool:
        return random.choice(ip_pool)
    return None

while True:
    conn,addr=s.accept()
    data=conn.recv(1024).decode().strip()
    if not data:
        conn.close()
        continue
    print(f"Client {addr} → {data}")

    if data=="DISCOVER":
        cname=addr[0]
        offer_ip=select_ip_for(cname)
        if offer_ip:
            conn.send(f"OFFER {offer_ip}".encode())
            print(f"[OFFER] {cname} ← {offer_ip}")
        else:
            conn.send("NO_IP_AVAILABLE".encode())
            print("[INFO] No IPs left to offer")

    elif data.startswith("REQUEST"):
        _,cname,req_ip=data.split()
        if req_ip not in ip_pool:
            conn.send("NACK".encode())
            print(f"[NACK] {cname} requested invalid IP {req_ip}")
        else:
            assigned[cname]=(req_ip,time.time()+lease_duration)
            past_leases[cname]=req_ip
            ip_pool.remove(req_ip)
            conn.send(f"ACK {req_ip}".encode())
            print(f"[ACK] {cname} assigned {req_ip}")

    elif data.startswith("RELEASE"):
        _,cname=data.split()
        if cname in assigned:
            ip,_=assigned.pop(cname)
            ip_pool.append(ip)
            conn.send(f"RELEASED {ip}".encode())
            print(f"[RELEASE] {cname} returned {ip}")
        else:
            conn.send("NOT_FOUND".encode())

    conn.close()
    print("\n--- CURRENT ASSIGNMENTS ---")
    if assigned:
        for cname,(ip,end) in assigned.items():
            print(f"{cname:10} → {ip} | {int(end-time.time())}s left")
    else:
        print("No active leases")
    print("----------------------------\n")