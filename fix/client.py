import socket
import threading
import os

ip = socket.gethostbyname(socket.gethostname())
port = 5500
size = 1024
alias = input("Pilih alias >> ")
klien = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
address = (ip, port)
klien.connect(address)

def klien_recvi():
    while True:
        try:
            pesan = klien.recv(1024).decode('utf-8')
            if pesan == "alias?":
                klien.send(alias.encode('utf-8'))
            elif pesan.startswith("[File '"):
                filename = pesan.split("'")[1]
                with open(filename, 'wb') as file:
                    while True:
                        data = klien.recv(size)
                        if not data or data == b"<END>":
                            break
                        file.write(data)
                print(f"File '{filename}' received from server.")
            else:
                print(pesan)
        except Exception as e:
            print(f'Error: {str(e)}')
            klien.close()
            break

def kirim():
    while True:
        pesan = input("Masukkan pesan (gunakan '@unicast alias pesan' untuk unicast, '@multicast alias1 alias2 pesan' untuk multicast, atau '@file:filename target_alias' untuk mengirim file) >> ")
        if pesan.lower().startswith('@unicast'):
            target_alias, pesan_unicast = pesan.split(' ', 2)[1:]
            pesan = f'@unicast {target_alias} {pesan_unicast}'
        elif pesan.lower().startswith('@multicast'):
            pesan_parts = pesan.split(' ', 3)
            target_aliases = " ".join(pesan_parts[1:3])
            pesan_multicast = pesan_parts[3]
            pesan = f'@multicast {target_aliases} {pesan_multicast}'
        elif pesan.lower().startswith('@file:'):
            pesan_parts = pesan.split(' ', 1)
            filename, target_alias = pesan_parts[0][6:], pesan_parts[1]
            filename = os.path.basename(filename)
            if not os.path.exists(filename):
                print(f"Error: File '{filename}' not found.")
                continue
            with open(filename, "rb") as file:
                klien.send(f'@file: {filename} {target_alias}'.encode('utf-8'))  # Kirim perintah @file ke server
                data = file.read(size)
                while data:
                    try:
                        klien.send(data)
                        data = file.read(size)
                    except ConnectionAbortedError:
                        print("Error: Connection with the server was aborted.")
                        break
                klien.send(b"<END>")  # Tandai akhir file yang dikirim
                print(f"File '{filename}' sent to {target_alias}.")
                continue
        klien.send(pesan.encode('utf-8'))

recive_thread = threading.Thread(target=klien_recvi)
recive_thread.start()

send_thread = threading.Thread(target=kirim)
send_thread.start()
