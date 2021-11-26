class RFC:
    def __init__(self, number, title, host):
        self.number = number
        self.title = title
        self.hostname = host
    
    def getRFCnumber(self):
        return self.number
    
    def getRFCtitle(self):
        return self.title
    
    def getRFChostname(self):
        return self.hostname
    