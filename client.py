import socket
import time
import uuid

mac = hex(uuid.getnode())[2:]
port = 6767
bcast = ("255.255.255.255", port)

def send_discover(sock):
    sock.sendto(f"DISCOVER {mac}".encode(), bcast)

def wait_offer(sock, timeout=5):
    sock.settimeout(timeout)
    try:
        data, addr = sock.recvfrom(1024)
        return data.decode().strip(), addr
    except:
        return None, None

def send_request(ip, server_addr):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(f"REQUEST {mac} {ip}".encode(), server_addr)
    s.settimeout(5)
    try:
        d,_ = s.recvfrom(1024)
        return d.decode().strip()
    except:
        return None

def send_renew(server_addr):
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.sendto(f"RENEW {mac}".encode(), server_addr)
    r.settimeout(5)
    try:
        d,_ = r.recvfrom(1024)
        return d.decode().strip()
    except:
        return None

def send_release(server_addr):
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.sendto(f"RELEASE {mac}".encode(), server_addr)
    r.settimeout(3)
    try:
        d,_ = r.recvfrom(1024)
        return d.decode().strip()
    except:
        return None

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

send_discover(sock)
msg, server_addr = wait_offer(sock, timeout=5)
if not msg:
    print("No OFFER received")
    sock.close()
    exit()

parts = msg.split()
if not (parts[0] == "OFFER" and parts[1] == mac):
    print("Unexpected OFFER:", msg)
    sock.close()
    exit()

offered_ip = parts[2]
print("[DISCOVER] OFFER received:", offered_ip, "from", server_addr)

ack = send_request(offered_ip, server_addr)
if not ack or not ack.startswith("ACK"):
    print("REQUEST failed or NACK")
    sock.close()
    exit()

print("[REQUEST] ACK received. Lease granted for", offered_ip)

lease_time = 30
lease_end = time.time() + lease_time
t1 = lease_end - lease_time / 2

while True:
    now = time.time()
    if now >= lease_end:
        print("Lease expired, restarting discovery")
        send_discover(sock)
        msg, server_addr = wait_offer(sock, timeout=5)
        if not msg:
            break
        parts = msg.split()
        if parts[0] != "OFFER":
            break
        offered_ip = parts[2]
        ack = send_request(offered_ip, server_addr)
        if not ack or not ack.startswith("ACK"):
            break
        lease_end = time.time() + lease_time
        t1 = lease_end - lease_time / 2
        continue

    if now >= t1:
        r = send_renew(server_addr)
        if r and r.startswith("ACK_RENEW"):
            lease_end = time.time() + lease_time
            t1 = lease_end - lease_time / 2
            print("[RENEW] success")
        else:
            print("[RENEW] failed, will try full discover on expiry")
            t1 = lease_end + 1

    time.sleep(1)
    if time.time() - lease_end > 1:
        continue

print("Releasing if possible")
res = send_release(server_addr)
print("Release response:", res)
sock.close()
