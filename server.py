import socket, threading, time

server_ip = "0.0.0.0"
server_port = 6767
pool = [f"192.168.1.{i}" for i in range(10, 251)]
leases = {}
lease_time = 15

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((server_ip, server_port))

def cleaner():
    while True:
        now = time.time()
        expired = [mac for mac, d in leases.items() if now > d["expiry"]]
        for mac in expired:
            del leases[mac]
        time.sleep(1)

threading.Thread(target=cleaner, daemon=True).start()

while True:
    data, addr = sock.recvfrom(1024)
    msg = data.decode()

    if msg.startswith("DISCOVER"):
        _, mac = msg.split()
        if mac in leases:
            ip = leases[mac]["ip"]
        else:
            ip = None
            for candidate in pool:
                if candidate not in [v["ip"] for v in leases.values()]:
                    ip = candidate
                    break
            if ip is None:
                continue
        offer = f"OFFER {ip} {lease_time}"
        sock.sendto(offer.encode(), addr)

    elif msg.startswith("REQUEST"):
        _, mac, req_ip = msg.split()
        leases[mac] = {"ip": req_ip, "expiry": time.time() + lease_time}
        ack = f"ACK {req_ip} {lease_time}"
        sock.sendto(ack.encode(), addr)

    elif msg.startswith("RENEW"):
        _, mac = msg.split()
        if mac in leases:
            leases[mac]["expiry"] = time.time() + lease_time
            ip = leases[mac]["ip"]
            rn = f"RENEWED {ip} {lease_time}"
            sock.sendto(rn.encode(), addr)

    elif msg.startswith("RELEASE"):
        _, mac, ip = msg.split()
        if mac in leases:
            del leases[mac]
        sock.sendto("RELEASED".encode(), addr)
