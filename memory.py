from exceptions import AddressError


class Memory:
    def __init__(self, block, start=0, offset=0):
        self.block = block
        self.start = start
        self.offset = offset
        self.current = 0
        self.min_addr = offset
        self.max_addr = offset + len(block)

    def next_byte(self):
        if self.current < len(self.block):
            b = self.block[self.current]
            self.current += 1
            return b
        return None

    def rewind(self):
        self.current = 0

    @property
    def addr(self):
        return self.current + self.offset

    @addr.setter
    def addr(self, value):
        if value < self.min_addr or value > self.max_addr:
            raise AddressError(f"invalide addr {value:04x}")
        self.current = value - self.offset

    def __len__(self):
        return len(self.block)

    def addr_in(self, addr):
        return self.min_addr <= addr <= self.max_addr

    def __getitem__(self, index):
        if isinstance(index, int):
            ofs = index - self.offset
            if ofs < 0 or ofs >= len(self.block):
                raise AddressError(f"{index:04x} out of range")
            return self.block[ofs]

        if not isinstance(index, slice):
            raise AddressError(f"invalide index {index!r}")

        start, stop = index.start, index.stop
        if start is None:
            start = 0
        else:
            start -= self.offset

        if stop is None:
            stop = len(self.block)
        else:
            stop -= self.offset
        if start < 0 or stop < 0 or stop > len(self.block) or start >= stop:
            raise AddressError(f"invalide index {index!r}")

        return self.block[start:stop]
