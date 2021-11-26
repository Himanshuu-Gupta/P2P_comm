import socket
from multiprocessing import Lock
from threading import Thread
import os
import time
import platform
from typing import OrderedDict
from RFC import RFC
from Peers import Peer

HOST_OS = platform.platform()
VERSION = "P2P-CI/1.0"
MAX_BUFFER_LEN = 4096
SERVER_PORT = 7734
MAX_RESPONSE_SIZE = 4096
MAX_REQUEST_SIZE = 4096
rfcs=OrderedDict()
peers=[]
lock_rfcs = Lock()
lock_peers = Lock()

STATUS_CODES = {
    "OK": ["200","OK"],
    "BAD_REQUEST": ["400", "Bad Request"],
    "NOT_FOUND": ["404","Not Found"],
    "VERSION_NOT_SUPPORTED": ["505","P2P-CI Version Not Supported"]
}

SERVER_ADD = "192.168.1.230"

def generate_response(conn, status, response_result):
    respmsg = VERSION +" " +STATUS_CODES[status][0] +" "+ STATUS_CODES[status][1]+"\r\n"+\
            +"\r\n"

    for response in response_result:
        respmsg = respmsg + response[0]+" "+response[1]+" "+response[2]+" "+response[3]+"\r\n"
    respmsg = respmsg + "\r\n"
    conn.sendall(respmsg.encode())

def is_peer_added(hostname, lock_peers, peers):
    lock_peers.acquire()
    for peer in peers:
        if peer.hostname == hostname:
            lock_peers.release()
            return True
    lock_peers.release()
    return False


def server_main_func(conn, client_add):
    try:
        while True:
            #Opening the connection to receive the data from the client
            data = conn.recv(MAX_BUFFER_LEN)
            if not data:
                break
            
            # Process the data received to get the header fields and data field values
            request = data.decode().split('\r\n')
            request_type = request[0].split()[0]
            rfc_version = request[0].split()[-1]
            client_hostname = request[1].split()[1]
            client_port = int(request[2].split()[1])
            final_response_result = []
            print(request_type, rfc_version, client_hostname, client_port)

            if request_type == "ADD":
                rfc_number = int(request[0].split()[2])
                rfc_title = request[3].split()[1]
                response_code = "OK"
                final_response_result.append(["RFC-"+str(rfc_number), str(rfc_title), str(client_hostname), str(client_port)])

                if rfc_version != VERSION:
                    response_code = "VERSION_NOT_SUPPORTED"
                else:
                    # Check if client (peer) is already active or not
                    is_peer_active_bool = is_peer_added(client_hostname, lock_peers, peers)
                    if not is_peer_active_bool:
                        new_peer = Peer(client_hostname, client_port)
                        lock_peers.acquire()
                        peers.insert(0, new_peer)
                        lock_peers.release()

                    new_rfc = RFC(rfc_number, rfc_title, client_hostname)

                    # Add RFC to RFCs list
                    lock_rfcs.acquire()
                    if rfc_number in rfcs.keys():
                        print("old")
                        # check if client has already added that RFC(avoid duplication)
                        already_present = False
                        for client in rfcs[rfc_number]:
                            if client.hostname == client_hostname:
                                already_present = True
                                break
                        if not already_present:
                            rfcs[rfc_number] = rfcs[rfc_number] + [new_rfc]
                    else:
                        print("new")
                        rfcs[rfc_number] = [new_rfc]
                    lock_rfcs.release()
                generate_response(conn, response_code, final_response_result)
            elif request_type == "LOOKUP":
                rfc_number = int(request[0].split()[2])
                rfc_title = request[3].split()[1]
                response_code = "OK"

                if rfc_version != VERSION:
                    response_code = "VERSION_NOT_SUPPORTED"
                else:
                    # Check if this RFC is present
                    lock_rfcs.acquire()
                    lock_peers.acquire()
                    print(rfc_title)
                    if rfc_number in rfcs.keys():
                        # If RFC is present add all hosts having this rfc to response_data
                        rfcs_list = rfcs[rfc_number]
                        print("test")
                        for rfc in rfcs_list:
                            for peer in peers:
                                if rfc.hostname == peer.hostname:
                                    final_response_result.append(["RFC-"+str(rfc_number), str(rfc_title), str(peer.hostname), str(peer.port)])
                    else:
                        response_code = "NOT_FOUND"
                    lock_peers.release()
                    lock_rfcs.release()
                    print("end")
                generate_response(conn, response_code, final_response_result)
            elif request_type == "LIST":
                response_code = "OK"
                lock_rfcs.acquire()
                lock_peers.acquire()
                for rfc_number in rfcs.keys():
                    rfcs_list = rfcs[rfc_number]
                    for rfc in rfcs_list:
                        for peer in peers:
                            if rfc.hostname == peer.hostname:
                                final_response_result.append(["RFC-"+str(rfc_number), str(rfc.title), str(peer.hostname), str(peer.port)])
                lock_peers.release()
                lock_rfcs.release()
                generate_response(conn, response_code, final_response_result)
           
    finally:
        # Close connection in the end
        print("Closing connection to ", client_add)

        lock_rfcs.acquire()
        for key, l in rfcs.copy().items():
            for each in l:
                if each.hostname == client_add[0]:
                    rfcs[key].remove(each)
            if not l:
                rfcs.pop(key)
                
        lock_rfcs.release()

        lock_peers.acquire()

        for each in peers.copy():
            if each.hostname == client_add[0]:
                peers.remove(each)
        lock_peers.release()

        conn.close()
        exit(0)

if __name__ == '__main__':
    spawned = []

    # Binding and listening to a socket.
    HOST_IP = socket.gethostbyname(SERVER_ADD)
    server_port = SERVER_PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST_IP, server_port))
    s.listen()
     
    while True:
        print('Waiting for clients on server: ' + HOST_IP)
        connection, client_address = s.accept()
        p = Thread(target=server_main_func, args=(connection, client_address))
        spawned.append(p)
        p.start()