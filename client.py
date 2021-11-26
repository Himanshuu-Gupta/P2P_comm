import socket
from multiprocessing import Lock
from threading import Thread
import os
import time
import platform
from time import gmtime, strftime

HOST_OS = platform.platform()
VERSION = "P2P-CI/1.0"
SERVER_PORT = 7734
MAX_RESPONSE_SIZE = 4096
MAX_REQUEST_SIZE = 4096
RFCS_PATH = "./RFCs/client1/"


STATUS_CODES = {
    "OK": ["200","OK"],
    "BAD_REQUEST": ["400", "Bad Request"],
    "NOT_FOUND": ["404","Not Found"],
    "VERSION_NOT_SUPPORTED": ["505","P2P-CI Version Not Supported"]
}

# SERVER_ADD = "71.69.165.236"
# CLIENT_ADD = "71.69.165.236"
SERVER_ADD = "192.168.1.230"
CLIENT_ADD = "192.168.1.230"
HOST_IP = socket.gethostbyname(CLIENT_ADD)

my_rfcs = list()
lock_my_rfcs = Lock()

socket_details = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_details.bind((CLIENT_ADD, 0))
upload_port = socket_details.getsockname()
print(upload_port)

def list_all_RFC(sock, upload_port):
    list_request = "LIST"+" "+"ALL "+VERSION+"\r\n" + \
                   "Host:"+" "+CLIENT_ADD+"\r\n" + \
                   "Port:"+" "+str(upload_port)+"\r\n" + \
                   "\r\n"

    sock.sendall(list_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()
    return response

def add_new_RFC(sock, rfc):
    rfc_title = rfc.split('.')[0]
    rfc_number = int(rfc_title[3:])
    add_request = "ADD"+" "+"RFC "+str(rfc_number)+" "+VERSION+"\r\n" + \
                  "Host:"+" "+CLIENT_ADD+"\r\n" + \
                  "Port:"+" "+str(upload_port)+"\r\n" + \
                  "Title:"+" "+rfc_title+"\r\n" + \
                  "\r\n"

    sock.sendall(add_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()

    if int((response.split('\r\n')[0]).split()[1]) == "OK":
        lock_my_rfcs.acquire()
        if rfc_number not in my_rfcs:
            my_rfcs.append(rfc_number)
        lock_my_rfcs.release()
    return response

def lookup_rfc(sock, rfc_number, rfc_title):
    lookup_request = "LOOKUP"+" "+"RFC "+str(rfc_number)+" "+VERSION+"\r\n" + \
                     "Host:"+" "+CLIENT_ADD+"\r\n" + \
                     "Port:"+" "+str(upload_port)+"\r\n" + \
                     "Title:"+" "+rfc_title+"\r\n" + \
                     "\r\n"

    sock.sendall(lookup_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()
    return response

# for each in STATUS_CODES:
#     print(STATUS_CODES[each][0], STATUS_CODES[each][1])
def serve_peers():
    socket_details.listen()

    while True:
        peer_sock, peer_address = socket_details.accept()
        request = peer_sock.recv(MAX_REQUEST_SIZE)
        if not request:
            continue

        request = request.decode().split('\r\n')
        request_row_1 = request[0].split()  
        rfc_number = int(request_row_1[2])
        version = request_row_1[-1]

        response_code = "OK"
        response = ""

        if version != VERSION:
            response_code = "VERSION_NOT_SUPPORTED"
        else:
            # check if requested RFC is present
            lock_my_rfcs.acquire() 
            if rfc_number not in my_rfcs :
                response_code = "NOT_FOUND"
            lock_my_rfcs.release()
                
            if response_code == "NOT_FOUND":
                response = VERSION+" "+str(response_code)+" "+STATUS_CODES[response_code]+"\r\n" +\
                            "\r\n"
            else:
                file_path = RFCS_PATH+'rfc'+str(rfc_number)+'.txt'
                current_time = strftime("%a, %d %b %Y %X GMT", gmtime())
                modified_time = strftime("%a, %d %b %Y %X GMT", time.localtime(os.path.getmtime(file_path)))
                with open(file_path, 'r') as my_file:
                    data = my_file.read()
                data_length = str(len(data))

                response = VERSION + " " + str(response_code) + " " + STATUS_CODES[response_code] + "\r\n" +\
                    "Date: " + current_time + "\r\n" +\
                    "OS: " + HOST_OS + "\r\n" +\
                    "Last-Modified: " + modified_time + "\r\n" +\
                    "Content-Length: " + data_length + "\r\n" +\
                    "Content Type: text/text\r\n" + \
                    data + "\r\n" +\
                    "\r\n"

        peer_sock.sendall(response.encode())
        peer_sock.close()
    

def rfc_download_request(rfc_number, hostname, port):
    download_request = "GET" + " RFC " + str(rfc_number) + " " + VERSION + "\r\n" +\
                "Host: " + hostname + "\r\n" +\
                "OS: " + HOST_OS + "\r\n" +\
                "\r\n"

    download_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_ip = socket.gethostbyname(hostname)
    download_sock.connect((host_ip, port))
    download_sock.sendall(download_request.encode())
    
    data = ''
    while True:
        response = download_sock.recv(MAX_RESPONSE_SIZE).decode()
        if not response:
            break
        data += response

    split_response = data.split('\r\n')
    content_len = int(split_response[4].split(':')[1])

    if int(split_response[0].split()[1]) != "OK":
        return '\r\n'.join(split_response[:6])

    data = data[-4-content_len:-4]

    file_path = RFCS_PATH+'rfc'+str(rfc_number)+'.txt'
    my_file = open(file_path, 'w')
    my_file.write(data)

    my_file.close()
    download_sock.close()
    
    return '\r\n'.join(split_response[:6])

def print_main_menu():
    print("1. ADD New RFC")
    print("2. LOOKUP RFC")
    print("3. LIST ALL RFC")
    print("4. Download RFC")
    print("5. DISCONNECT")

if __name__ == '__main__':
    # Spawn a new thread to serve other peers
    p_serve_peers = Thread(target=serve_peers)
    p_serve_peers.daemon = True
    p_serve_peers.start()

    SERVER_IP = socket.gethostbyname(SERVER_ADD)
    print("Establishing Connection to - "+SERVER_IP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))

    while True:
        print_main_menu()
        option = int(input("Main Menu:"))
        if option == 1:
            rfc = input("\nEnter filename: ")
            response = add_new_RFC(sock, rfc)
            print("Add RFC " + str(rfc) + "\n\nServer Response:\n" + response)
        elif option == 2:
            lookup_rfc_number = input("\nEnter RFC number to lookup for: ")
            lookup_rfc_title = 'rfc'+str(lookup_rfc_number) 
            response = lookup_rfc(sock, lookup_rfc_number, lookup_rfc_title)
            print("Lookup RFC "+ str(lookup_rfc_number) + "\nServer Response:\n" + response)
        elif option == 3:
            response = list_all_RFC(sock, upload_port)
            print("LIST RFC\n\nServer Response:\n" + response)
        elif option == 4:
            download_rfc_number = input("\nEnter RFC number: ")
            get_rfc_from = input("Enter host: ")
            get_rfc_from_port = int(input("Enter port: "))
            response = rfc_download_request(download_rfc_number, get_rfc_from, get_rfc_from_port)
            print("Download RFC\n\nServer Response:\n" + response)
        elif option == 5:
            sock.close()
            exit(0)



