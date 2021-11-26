class Peer:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
    
    def getPeerhostname(self):
        return self.hostname
    
    def getPeerportnumber(self):
        return self.port
    