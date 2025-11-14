import socket, time, uuid

server_ip = "127.0.0.1"
server_port = 6767
mac = uuid.uuid4().hex[:12]
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)

assigned_ip = None
renew_count = 0
max_renews = 2

def send_release():
    if assigned_ip:
        msg = f"RELEASE {mac} {assigned_ip}"
        sock.sendto(msg.encode(), (server_ip, server_port))

try:
    msg = f"DISCOVER {mac}"
    sock.sendto(msg.encode(), (server_ip, server_port))
    data, _ = sock.recvfrom(1024)
    offer, offer_ip, lt = data.decode().split()
    msg = f"REQUEST {mac} {offer_ip}"
    sock.sendto(msg.encode(), (server_ip, server_port))
    data, _ = sock.recvfrom(1024)
    _, assigned_ip, lt = data.decode().split()

    while renew_count < max_renews:
        time.sleep(int(lt) // 2)
        msg = f"RENEW {mac}"
        sock.sendto(msg.encode(), (server_ip, server_port))
        data, _ = sock.recvfrom(1024)
        _, _, lt = data.decode().split()
        renew_count += 1

    time.sleep(int(lt))

finally:
    send_release()
    sock.close()
