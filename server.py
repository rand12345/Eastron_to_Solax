from machine import UART


class UARTClass():
    def __init__(self, address, port: int, baudrate=115200,
                 parity=None, stop_bits=1,
                 data_bits=8, timeout=5, tries=3):

        self.serline = UART(port, baudrate)
        self.baudrate = baudrate
        self.parity = 0
        self.stop_bits = stop_bits
        self.data_bits = data_bits
        self.timeout = timeout
        self.tries = tries
        self.address = address

        self.serline.init(self.baudrate, bits=8, parity=None, stop=1)

    def send(self, request):
        self.serline.write(request)
