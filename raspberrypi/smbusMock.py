class SMBus:
    def __init__(self, port):
        self.port = port

    def open(self, bus, device):
        pass

    def close(self):
        pass

    def write_byte(self, address, value):
        pass

    def write_byte_data(self, address, register, value):
        pass

    def write_block_data(self, address, register, value):
        pass

    def read_byte(self, address):
        return 0

    def read_byte_data(self, address, register):
        return 0

    def read_block_data(self, address, register):
        return 0