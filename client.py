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
RFCS_PATH = "./RFC/download/"


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
upload_port = socket_details.getsockname()[1]
#print("Port Details",upload_port)

def list_all_RFC(sock, upload_port):
    # "\r shows the carriage return and \n shows the new line in the generated response" 
    list_request = "LIST"+" "+"ALL "+VERSION+"\r\n" + \
                   "Host:"+" "+CLIENT_ADD+"\r\n" + \
                   "Port:"+" "+str(upload_port)+"\r\n" + \
                   "\r\n"
    print("\n~~~~~~ Request Generated to sent to server~~~~~~ \n", list_request)
    sock.sendall(list_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()
    print("\n~~~~~~~~Response received from server~~~~~~~~~\n",response)
    return response

def add_new_RFC(sock, rfc_title, rfc_number):
    #rfc_title = rfc.split('-')[0]
    #rfc_number = int(rfc_title[4:])
    print("\n RFC number - ", rfc_number, rfc_title)
    add_request = "ADD"+" "+"RFC "+str(rfc_number)+" "+VERSION+"\r\n" + \
                  "Host:"+" "+CLIENT_ADD+"\r\n" + \
                  "Port:"+" "+str(upload_port)+"\r\n" + \
                  "Title:"+" "+rfc_title+"\r\n" + \
                  "\r\n"
    print("\n~~~~~~ Request Generated to sent to server~~~~~~ \n", add_request)
    sock.sendall(add_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()
    print("\n~~~~~~~~Response received from server~~~~~~~~~\n",response)
    if int((response.split('\r\n')[0]).split()[1]) == STATUS_CODES["OK"][0]:
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
    print("\n~~~~~~ Request Generated to sent to server~~~~~~ \n", lookup_request)
    sock.sendall(lookup_request.encode())
    response = sock.recv(MAX_RESPONSE_SIZE).decode()
    print("\n~~~~~~~~Response received from server~~~~~~~~~\n",response)
    return response

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
    

def rfc_download_request(sock, rfc_number, hostname, port):
    download_request = "GET" + " RFC " + str(rfc_number) + " " + VERSION + "\r\n" +\
                "Host: " + hostname + "\r\n" +\
                "Port:"+" "+str(port)+"\r\n" + \
                "OS: " + HOST_OS + "\r\n" +\
                "\r\n"
    print("\n~~~~~~ Request Generated to sent to server~~~~~~ \n", download_request)
    # download_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # host_ip = socket.gethostbyname(hostname)
    # download_sock.connect((host_ip, port))
    sock.sendall(download_request.encode())
    
    data = sock.recv(MAX_RESPONSE_SIZE).decode()
    # while True:
    #     response = sock.recv(MAX_RESPONSE_SIZE).decode()
    #     if not response:
    #         break
    #     data += response
    print("\n~~~~~~~~Response received from server~~~~~~~~~\n",data)
    split_response = data.split('\r\n')
    print("Response",split_response[0])
    if "OK" in split_response[0]:
    # Opening the file path and writing contents to the file 
        isExist = os.path.exists(RFCS_PATH)
        if not isExist:
            # Create a new download directory in the client folder
            os.makedirs(RFCS_PATH)
            print("Creating a download directory in ./RFC/download in the current client directory")
        file_path = RFCS_PATH+'rfc'+str(rfc_number)+'.txt'
        my_file = open(file_path, 'w')
        my_file.write(data)
        my_file.close()
    # download_sock.close()
    return '\r\n'.join(split_response[:6])

def print_main_menu():
    print("~~~~~~~Main Menu~~~~~~")
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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    print("Establishing Connection to - "+SERVER_IP)
    while True:
        print_main_menu()
        option = int(input("\nSelect option from above menu - "))
        if option == 1:
            rfcnum = input("\nEnter RFC number (e.g-\"532\"): ")
            rfctitle = 'RFC-'+str(rfcnum)
            response = add_new_RFC(sock, rfctitle, rfcnum)
        elif option == 2:
            print("Enter only RFC number you are looking for e.g. for RFC-2, please enter \"2\" - ")
            lookup_rfc_number = input("\nEnter RFC number to lookup for: ")
            lookup_rfc_title = 'RFC-'+str(lookup_rfc_number) 
            response = lookup_rfc(sock, lookup_rfc_number, lookup_rfc_title)
        elif option == 3:
            response = list_all_RFC(sock, upload_port)
        elif option == 4:
            download_rfc_number = input("\nEnter RFC number to download:")
            get_rfc_host = input("Enter host: ")
            get_rfc_port = int(input("Enter port: "))
            response = rfc_download_request(sock, download_rfc_number, get_rfc_host, get_rfc_port)
        elif option == 5:
            sock.close()
            exit(0)



