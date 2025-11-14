import socket, threading, time, random

server_ip = "0.0.0.0"
server_port = 6767
pool = [f"192.168.1.{i}" for i in range(10, 21)]
leases = {}
lease_time = 15

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind((server_ip, server_port))

def cleaner():
    while True:
        now = time.time()
        expired = [mac for mac,d in leases.items() if now > d["expiry"]]
        for mac in expired:
            ip = leases[mac]["ip"]
            del leases[mac]
            print(f"[CLEANER] expired {mac} -> {ip}")
        time.sleep(1)

threading.Thread(target=cleaner, daemon=True).start()

print(f"SERVER STARTED, listening on UDP {server_port}")

while True:
    try:
        data, addr = sock.recvfrom(1024)
    except Exception as e:
        print("recvfrom error:", e)
        continue

    if not data:
        continue

    msg = data.decode().strip()
    print(f"[RECV] from {addr}: {msg}")

    if msg.startswith("DISCOVER"):
        parts = msg.split()
        if len(parts) < 2:
            print("[WARN] DISCOVER missing mac")
            continue
        _, mac = parts[:2]
        if mac in leases:
            ip = leases[mac]["ip"]
        else:
            ip = None
            for candidate in pool:
                used = {v["ip"] for v in leases.values()}
                if candidate not in used:
                    ip = candidate
                    break
            if ip is None:
                sock.sendto("NO_IP".encode(), addr)
                print("[OFFER] none available")
                continue
        offer = f"OFFER {mac} {ip} {lease_time}"
        sock.sendto(offer.encode(), addr)
        print(f"[OFFER] {mac} -> {ip} to {addr}")

    elif msg.startswith("REQUEST"):
        parts = msg.split()
        if len(parts) < 3:
            print("[WARN] REQUEST malformed")
            continue
        _, mac, req_ip = parts[:3]
        leases[mac] = {"ip": req_ip, "expiry": time.time() + lease_time}
        ack = f"ACK {mac} {req_ip} {lease_time}"
        sock.sendto(ack.encode(), addr)
        print(f"[ACK] {mac} -> {req_ip}")

    elif msg.startswith("RENEW"):
        parts = msg.split()
        if len(parts) < 2:
            continue
        _, mac = parts[:2]
        if mac in leases:
            leases[mac]["expiry"] = time.time() + lease_time
            ip = leases[mac]["ip"]
            rn = f"RENEWED {mac} {ip} {lease_time}"
            sock.sendto(rn.encode(), addr)
            print(f"[RENEW-ACK] {mac} -> {ip}")
        else:
            sock.sendto("NACK".encode(), addr)
            print(f"[RENEW-NACK] {mac} not found")

    elif msg.startswith("RELEASE"):
        parts = msg.split()
        if len(parts) < 3:
            continue
        _, mac, ip = parts[:3]
        if mac in leases:
            del leases[mac]
            print(f"[RELEASE] {mac} -> {ip}")
        sock.sendto("RELEASED".encode(), addr)
