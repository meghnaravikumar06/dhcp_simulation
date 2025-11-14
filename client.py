import socket, time, uuid

server_port = 6767
mac = uuid.uuid4().hex[:12]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(5)
broadcast = ("255.255.255.255", server_port)

assigned_ip = None
try:
    sock.sendto(f"DISCOVER {mac}".encode(), broadcast)
    data, server = sock.recvfrom(1024)
    parts = data.decode().split()
    if parts[0] != "OFFER":
        print("No valid OFFER:", data.decode())
        raise SystemExit
    assigned_ip = parts[2]
    lease_time = int(parts[3])
    print(f"[OFFER] {assigned_ip} lease={lease_time}")

    sock.sendto(f"REQUEST {mac} {assigned_ip}".encode(), server)
    data, server = sock.recvfrom(1024)
    parts = data.decode().split()
    print(f"[ACK] {parts}")

    renew_count = 0
    MAX_RENEWS = 2
    while renew_count < MAX_RENEWS:
        time.sleep(lease_time // 2)
        sock.sendto(f"RENEW {mac}".encode(), server)
        data, server = sock.recvfrom(1024)
        parts = data.decode().split()
        print(f"[RENEW] {parts}")
        renew_count += 1

    print("Stopping renewals, waiting for lease expiry")
    time.sleep(lease_time + 1)

finally:
    if assigned_ip:
        try:
            sock.sendto(f"RELEASE {mac} {assigned_ip}".encode(), server)
            data, _ = sock.recvfrom(1024)
            print("[RELEASE] server replied:", data.decode())
        except:
            pass
    sock.close()
    print("client exiting")
