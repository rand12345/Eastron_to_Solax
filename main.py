from umodbus.serial import Serial as ModbusRTUMaster
from umodbus.modbus import ModbusRTU
import time

# import struct
from machine import UART

# Change this to False to disable energy history registers
experimental = True

# Used for serial link to server
class UARTClass:
    def __init__(
        self,
        port: int,
        baudrate: int,
    ):
        self.serline = UART(port, baudrate)
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
    ## https://owen-brothers.co.uk/pub/media/wysiwyg/OB737-CT_User_Manual.pdf
    OB737_active_power = 0x96  # <- OB737 # SDM230 0C, 12+1 = read 13 and 14 registor
    OB737_export_active_energy = 0x0900  # (kWh)
    OB737_import_active_energy = 0x0800  # (kWh)

    # values for SDM230 sinle phase Solax meter
    ## https://midsummerwholesale.co.uk/pdfs/Solax-meter-chint-Datasheet.pdf
    SDM230_active_power = 0xC  # 12 + 1
    SDM230_export_active_energy = 0x4B  # 74 + 1 in hex (kWh)
    SDM230_import_active_energy = 0x49  # 72 + 1 in hex (kWh)

    print("Performing inital test readings")

    print(f"Reading grid power register {OB737_active_power}")
    active_power = meter.read_input_registers(
        slave_addr=meter_addr,
        starting_addr=OB737_active_power,
        register_qty=2,
        signed=True,
    )
    active_power = active_power * 1000
    print(f"Status of hreg {meter_addr}: {active_power}W (grid power)\n")

    # new feature enabled?
    if experimental:
        print(f"Reading grid export register {OB737_export_active_energy}")
        export_active_energy = meter.read_input_registers(
            slave_addr=meter_addr,
            starting_addr=OB737_export_active_energy,
            register_qty=2,
            signed=True,
        )
        print(f"Status of hreg {meter_addr}: {export_active_energy}kWh (grid export)\n")

        print(f"Reading grid import register {OB737_import_active_energy}")
        import_active_energy = meter.read_input_registers(
            slave_addr=meter_addr,
            starting_addr=OB737_import_active_energy,
            register_qty=2,
            signed=True,
        )
        print(f"Status of hreg {meter_addr}: {import_active_energy}kWh (grid import)\n")

    print(client._register_dict)
    time.sleep(0.2)
    while True:
        try:
            # Read Modbus Request
            client.process()
            # time.sleep(0.25)
            # Request watt from meter
            active_power = meter.read_input_registers(
                slave_addr=meter_addr,
                starting_addr=OB737_active_power,
                register_qty=2,
                signed=True,
            )

            active_power = active_power * 1000
            # RS485 to server ascii
            ser.send(str(active_power) + "\n")
            reg_HREGS[14] = [int(active_power)]
            print(f"Status of hreg {meter_addr}: {reg_HREGS[14]}W (grid value)")

            # new feature enabled?
            if experimental:
                export_active_energy = meter.read_input_registers(
                    slave_addr=meter_addr,
                    starting_addr=OB737_export_active_energy,
                    register_qty=2,
                    signed=True,
                )
                reg_HREGS[76] = [int(export_active_energy)]
                print(
                    f"Status of hreg {meter_addr}: {reg_HREGS[76]}kWh (exported value)"
                )

                import_active_energy = meter.read_input_registers(
                    slave_addr=meter_addr,
                    starting_addr=OB737_import_active_energy,
                    register_qty=2,
                    signed=True,
                )
                reg_HREGS[78] = [int(import_active_energy)]
                print(
                    f"Status of hreg {meter_addr}: {reg_HREGS[78]}kWh (imported value"
                )

        except Exception:
            print("Lazily ignored errors")

        time.sleep(0.3)
        # end of loop


if __name__ == "__main__":
    # UART 3 -> Server serial RS485
    ser = UARTClass(port=3, baudrate=115200)
    print("MAIN")
    main()
