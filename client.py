import socket
import os
import time
import platform

HOST_OS = platform.platform()
VERSION = "P2P-CI/1.0"
SERVER_PORT = 7734
MAX_RESPONSE_SIZE = 4096
MAX_REQUEST_SIZE = 4096


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


socket_details = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket_details.bind((CLIENT_ADD, 0))
my_upload_port = socket_details.getsockname()
print(my_upload_port)

def list_all_RFC():
    pass

def add_new_RFC():
    pass





