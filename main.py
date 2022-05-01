from umodbus.serial import Serial as ModbusRTUMaster
from umodbus.modbus import ModbusRTU
from machine import UART
import time
import struct


class UARTClass:
    def __init__(
        self,
        address,
        port: int,
        baudrate=115200,
        parity=None,
        stop_bits=1,
        data_bits=8,
        timeout=5,
        tries=3,
    ):

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


def main():

    # act as client, provide Modbus data via RTU to a host device
    # uart=1 (A9, A10) # (TX, RX)
    modbus_addr_slave = 1  # address on bus as client
    client = ModbusRTU(
        addr=modbus_addr_slave,
        uart_id=2,  # UART ID for STM32
        baudrate=9600,  # optional, default 9600
        data_bits=8,  # optional, default 7
        stop_bits=1,  # optional, default 1
        parity=None,
        name="solax",
    )

    register_definitions = {
        "HREGS": {
            "1_HREG": {
                "register": 14,
                "len": 1,
            },
            "2_HREG": {
                "register": 11,
                "len": 1,
            },
            "3_HREG": {
                "register": 8,
                "len": 4,
            },
        },
    }

    client.setup_registers(registers=register_definitions, use_default_vals=True)
    reg_HREGS = client._register_dict["HREGS"]
    print(reg_HREGS)

    # uart=2 (A2, A3) # (TX, RX)
    meter_addr = 1  # bus address of client
    meter = ModbusRTUMaster(
        uart_id=1,  # UART ID for STM32
        baudrate=9600,  # optional, default 9600
        data_bits=8,  # optional, default 7
        stop_bits=1,  # optional, default 1
        parity=None,  # optional, default None
        pins=None,
        name="meter",
    )

    # READ HREGS read_holding_registers from Meter
    watt_register = 0x96  # 00 0C, 12+1 = read 13 and 14 registor
    watt_value = meter.read_input_registers(
        slave_addr=meter_addr, starting_addr=watt_register, register_qty=2, signed=True
    )
    watt_value = watt_value * 1000

    print(f"Status of hreg {meter_addr}: {watt_value}")
    # print(watt_value)
    print(client._register_dict)
    time.sleep(0.2)
    while True:
        # Read Modbus Request
        client.process()
        # time.sleep(0.25)
        # Request watt from meter
        watt_value = meter.read_input_registers(
            slave_addr=meter_addr,
            starting_addr=watt_register,
            register_qty=2,
            signed=True,
        )
        watt_value = watt_value * 1000
        # RS485 to server ascii
        ser.send(str(watt_value) + "\n")
        # Convert Float to Int
        watt = int(watt_value)
        # write Data int the Modbus register, that get read by Solax Invertor
        reg_HREGS[14] = [watt]

        print(f"Status of hreg {meter_addr}: {reg_HREGS[14]}")

        time.sleep(0.3)


if __name__ == "__main__":
    # port=2, address=2
    ser = UARTClass(port=3, address=2)
    print("MAIN")
    main()
