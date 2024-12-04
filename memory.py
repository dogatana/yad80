class Memory:
    def __init__(self, block, ofs=0):
        self.block = block
        self.ofs = 0

    def next_byte(self):
        if self.ofs < len(self.block):
            b = self.block[self.ofs]
            self.ofs += 1
            return b
        return None

    def rewind(self):
        self.ofs = 0

    def __getitem__(self, index):
        return self.block[index]
