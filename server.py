import socket
import time
import threading

ip_pool = ["192.168.1.10", "192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15", "192.168.1.16", "192.168.1.17", "192.168.1.18", "192.168.1.19", "192.168.1.20"]
assigned = {}
lease_duration = 10
server_ip = "0.0.0.0"
port = 9999

def lease_cleaner():
    while True:
        current_time = time.time()
        expired = [c for c, (_, end) in assigned.items() if current_time > end]
        for cname in expired:
            ip, _ = assigned.pop(cname)
            ip_pool.append(ip)
            print(f"[LEASE EXPIRED] {cname} released {ip}")
        time.sleep(1)

threading.Thread(target=lease_cleaner, daemon=True).start()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((server_ip, port))
s.listen(5)

print("DHCP SERVER SIMULATION STARTED")
print(f"Lease time for IPs: {lease_duration} seconds\n")
print("Waiting for clients...\n")

while True:
    conn, addr = s.accept()
    data = conn.recv(1024).decode().strip()
    if not data:
        conn.close()
        continue
    print(f"Client {addr} says: {data}")

    if data == "DISCOVER":
        if ip_pool:
            offer_ip = ip_pool[0]
            conn.send(f"OFFER {offer_ip}".encode())
            print(f"[OFFER] Offered IP {offer_ip} to {addr}")
        else:
            conn.send("NO_IP_AVAILABLE".encode())
            print("[INFO] No IPs left to offer!")

    elif data.startswith("REQUEST"):
        parts = data.split()
        if len(parts) == 3:
            _, cname, req_ip = parts
            assigned[cname] = (req_ip, time.time() + lease_duration)
            if req_ip in ip_pool:
                ip_pool.remove(req_ip)
            conn.send(f"ACK {req_ip}".encode())
            print(f"[ACK] {cname} assigned IP {req_ip} for {lease_duration}s")

    elif data.startswith("RELEASE"):
        parts = data.split()
        if len(parts) == 2:
            _, cname = parts
            if cname in assigned:
                old_ip, _ = assigned.pop(cname)
                ip_pool.append(old_ip)
                conn.send(f"RELEASED {old_ip}".encode())
                print(f"[RELEASE] {cname} released {old_ip}")
            else:
                conn.send("NOT_FOUND".encode())

    conn.close()
    print("\n--- Current IP Table ---")
    if assigned:
        for c, (ip, end) in assigned.items():
            print(f"{c:10} → {ip} | lease ends in {int(end - time.time())}s")
    else:
        print("No clients connected right now.")
    print("-------------------------\n")
