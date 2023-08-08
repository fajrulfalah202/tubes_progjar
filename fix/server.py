import socket
import threading
import os

ip = socket.gethostbyname(socket.gethostname())
port = 5500

address = (ip, port)
size = 1024
kliens = []
aliases = []
lock = threading.Lock()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(address)
server.listen()
FORMAT = "utf-8"
server_data_path = "server_data"

def broadcast(pesan, sender_alias=None):
    for klien in kliens:
        if sender_alias and aliases[kliens.index(klien)] == sender_alias:
            continue
        klien.send(pesan)

def multicast(pesan, sender_alias, target_aliases):
    for klien in kliens:
        alias = aliases[kliens.index(klien)]
        if alias in target_aliases and alias != sender_alias:
            klien.send(pesan)

def uni(pesan, sender_alias, target_alias):
    if target_alias in aliases:
        target_klien = kliens[aliases.index(target_alias)]
        target_klien.send(pesan)

def handle_client(klien):
    alias = aliases[kliens.index(klien)]
    while True:
        try:
            pesan = klien.recv(1024)
            if pesan:
                pesan_str = pesan.decode(FORMAT)
                if pesan_str.startswith("@unicast"):
                    target_alias, pesan_unicast = pesan_str.split(" ", 2)[1:]
                    pesan = f"[Unicast from {alias}]: {pesan_unicast}".encode(FORMAT)
                    uni(pesan, alias, target_alias)
                elif pesan_str.startswith("@multicast"):
                    pesan_parts = pesan_str.split(" ", 3)
                    target_aliases = " ".join(pesan_parts[1:3])
                    pesan_multicast = pesan_parts[3]
                    pesan = f"[Multicast from {alias}]: {pesan_multicast}".encode(FORMAT)
                    multicast(pesan, alias, target_aliases)
                elif pesan_str.startswith("@file:"):
                    pesan_parts = pesan_str.split(' ', 2)
                    filename, target_alias = pesan_parts[1], pesan_parts[2]
                    filename = os.path.basename(filename)
                    with open(os.path.join(server_data_path, filename), "wb") as file:
                        while True:
                            data = klien.recv(size)
                            if data == b"<END>":
                                break
                            file.write(data)
                            file.flush()
                    pesan = f"[File '{filename}' from {alias}]: File received and saved on server.".encode(FORMAT)
                    uni(pesan, alias, target_alias)

                    # Tambahkan kode untuk mengirim file ke klien target
                    send_file_to_client(target_alias, filename)
                else:
                    pesan = f"[Broadcast from {alias}]: {pesan_str}".encode(FORMAT)
                    broadcast(pesan, alias)
        except:
            index = kliens.index(klien)
            klien.close()
            alias = aliases[index]
            aliases.remove(alias)
            kliens.remove(klien)
            broadcast(f'[Server]: {alias} telah meninggalkan chat room.'.encode(FORMAT))
            break

def send_file_to_client(target_alias, filename):
    target_klien = None
    for klien, alias in zip(kliens, aliases):
        if alias == target_alias:
            target_klien = klien
            break

    if target_klien:
        try:
            with open(os.path.join(server_data_path, filename), "rb") as file:
                data = file.read(size)
                while data:
                    target_klien.send(data)
                    data = file.read(size)
                target_klien.send(b"<END>")
                print(f"File '{filename}' sent to {target_alias}.")
        except Exception as e:
            print(f"Error sending file to {target_alias}: {str(e)}")
    else:
        print(f"Target client with alias '{target_alias}' not found.")

def accept_connections():
    while True:
        print("Server berjalan dan mendengarkan...")
        klien, address = server.accept()
        print(f'Koneksi telah diterima dari {str(address)}')
        klien.send('alias?'.encode(FORMAT))
        alias = klien.recv(1024).decode(FORMAT)
        aliases.append(alias)
        kliens.append(klien)
        print(f'Alias dari klien ini adalah: {alias}')
        broadcast(f'[Server]: {alias} bergabung di chat room.'.encode(FORMAT))

        thread = threading.Thread(target=handle_client, args=(klien,))
        thread.start()

def address_of_client(target_alias):
    for klien, alias in zip(kliens, aliases):
        if alias == target_alias:
            return klien.getpeername()

    return None

if __name__ == "__main__":
    if not os.path.exists(server_data_path):
        os.makedirs(server_data_path)
    accept_connections()
