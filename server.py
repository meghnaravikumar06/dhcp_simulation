import socket
import time
import threading
import random

ip_pool = ["192.168.1.10","192.168.1.11","192.168.1.12","192.168.1.13","192.168.1.14","192.168.1.15","192.168.1.16","192.168.1.17","192.168.1.18","192.168.1.19","192.168.1.20"]

assigned = {}      
past_leases = {}  
lease_time = 30
port = 6767

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(("", port))

def cleaner():
    while True:
        now = time.time()
        expired = [m for m,(ip,e) in assigned.items() if e <= now]
        for m in expired:
            ip,_ = assigned.pop(m)
            ip_pool.append(ip)
            print(f"[LEASE EXPIRED] {m} -> {ip}")
        time.sleep(1)

threading.Thread(target=cleaner, daemon=True).start()

def select_ip(mac):
    if mac in past_leases:
        old = past_leases[mac]
        if old in ip_pool:
            return old
    if ip_pool:
        return random.choice(ip_pool)
    return None

print("SERVER RUNNING ON UDP PORT", port)

while True:
    try:
        data, addr = s.recvfrom(1024)
        msg = data.decode().strip()
    except:
        continue

    parts = msg.split()
    if not parts:
        continue

    if parts[0] == "DISCOVER" and len(parts) == 2:
        mac = parts[1]
        ip = select_ip(mac)
        if ip:
            s.sendto(f"OFFER {mac} {ip}".encode(), addr)
            print(f"[OFFER] {mac} -> {ip} to {addr}")
        else:
            s.sendto("NO_IP".encode(), addr)
            print("[OFFER] none available")

    elif parts[0] == "REQUEST" and len(parts) == 3:
        mac = parts[1]
        req_ip = parts[2]
        already_assigned = (mac in assigned and assigned[mac][0] == req_ip)
        if req_ip in ip_pool or already_assigned:
            assigned[mac] = (req_ip, time.time() + lease_time)
            past_leases[mac] = req_ip
            if req_ip in ip_pool:
                ip_pool.remove(req_ip)
            s.sendto(f"ACK {mac} {req_ip}".encode(), addr)
            print(f"[ACK] {mac} -> {req_ip}")
        else:
            s.sendto("NACK".encode(), addr)
            print(f"[NACK] {mac} requested {req_ip}")

    elif parts[0] == "RENEW" and len(parts) == 2:
        mac = parts[1]
        if mac in assigned:
            ip, _ = assigned[mac]
            assigned[mac] = (ip, time.time() + lease_time)
            s.sendto(f"ACK_RENEW {mac} {ip}".encode(), addr)
            print(f"[RENEW-ACK] {mac} -> {ip}")
        else:
            s.sendto("NACK".encode(), addr)
            print(f"[RENEW-NACK] {mac} not found")

    elif parts[0] == "RELEASE" and len(parts) == 2:
        mac = parts[1]
        if mac in assigned:
            ip,_ = assigned.pop(mac)
            ip_pool.append(ip)
            s.sendto(f"RELEASED {mac} {ip}".encode(), addr)
            print(f"[RELEASE] {mac} -> {ip}")
        else:
            s.sendto("NOT_FOUND".encode(), addr)
            print(f"[RELEASE] {mac} not found")
