import bluetooth
import time
from lab1 import Lab1

# Manually define missing constants
_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6
_IRQ_PERIPHERAL_CONNECT = 7
_IRQ_PERIPHERAL_DISCONNECT = 8
_IRQ_GATTC_SERVICE_RESULT = 9
_IRQ_GATTC_CHARACTERISTIC_RESULT = 11
_IRQ_GATTC_NOTIFY = 18

IAM = "Receiver"
IAM_SENDING_TO = "Transmitter"
BLE_NAME = IAM
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)

SEND_MESSAGES = [
    "EnableOFF DepthOFF",
    "EnableOFF DepthON",
    "EnableON DepthOFF",
    "EnableON DepthON"
]

class BLECentral:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.bt_irq)
        self.conn_handle = None
        self.rx_handle = None
        self.connected = False
        self.message_count = 0
        self.lab1 = Lab1()

    def bt_irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            name = self.decode_name(adv_data)
            if name == IAM_SENDING_TO:
                print(f"Found device: {name}")
                self.ble.gap_scan(None)  # Stop scanning
                self.ble.gap_connect(addr_type, addr)
        elif event == _IRQ_SCAN_DONE:
            print("Scan completed.")
        elif event == _IRQ_PERIPHERAL_CONNECT:
            conn_handle, addr_type, addr = data
            self.conn_handle = conn_handle
            self.connected = True
            print(f"Connected to {IAM_SENDING_TO}")
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            print("Disconnected")
            self.connected = False
            self.conn_handle = None
            self.rx_handle = None
            self.ble.gap_scan(2000, 30000, 30000)
        elif event == _IRQ_GATTC_SERVICE_RESULT:
            conn_handle, start_handle, end_handle, uuid = data
            if uuid == BLE_SVC_UUID:
                self.start_handle = start_handle
                self.end_handle = end_handle
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            conn_handle, def_handle, value_handle, properties, uuid = data
            if uuid == BLE_CHARACTERISTIC_UUID:
                self.rx_handle = value_handle
        elif event == _IRQ_GATTC_NOTIFY:
            conn_handle, value_handle, notify_data = data
            self.handle_rx(notify_data)

    def decode_name(self, adv_data):
        n = 0
        while n < len(adv_data):
            length = adv_data[n]
            if length == 0:
                return None
            type = adv_data[n + 1]
            if type == 0x09:  # Complete Local Name
                return adv_data[n + 2: n + 1 + length].decode()
            n += 1 + length
        return None

    def start_scan(self):
        print("Scanning...")
        self.ble.gap_scan(5000, 30000, 30000)

    def discover_services(self):
        if self.conn_handle is not None:
            self.ble.gattc_discover_services(self.conn_handle)

    def discover_characteristics(self):
        if self.conn_handle is not None:
            self.ble.gattc_discover_characteristics(
                self.conn_handle, self.start_handle, self.end_handle
            )

    def enable_notifications(self):
        if self.conn_handle is not None and self.rx_handle is not None:
            # CCCD is handle+1
            self.ble.gattc_write(self.conn_handle, self.rx_handle + 1, b'\x01\x00', 1)

    def handle_rx(self, data):
        try:
            message = data.decode()
            print(f"{IAM} received: {message}, count: {self.message_count}")
            self.message_count += 1

            if message == "EnableON DepthON":
                self.lab1.setDepthHigh()
                self.lab1.setEnableHigh()
            elif message == "EnableOFF DepthON":
                self.lab1.setDepthHigh()
                self.lab1.setEnableLow()
            elif message == "EnableON DepthOFF":
                self.lab1.setDepthLow()
                self.lab1.setEnableHigh()
            elif message == "EnableOFF DepthOFF":
                self.lab1.setDepthLow()
                self.lab1.setEnableLow()
            else:
                print("Unknown message received.")

        except Exception as e:
            print("Error decoding message:", e)

    def run(self):
        self.start_scan()
        while True:
            if self.connected and self.rx_handle is not None:
                # already subscribed, just wait
                time.sleep_ms(100)
            elif self.connected and self.rx_handle is None:
                self.discover_services()
                time.sleep(1)
                self.discover_characteristics()
                time.sleep(1)
                self.enable_notifications()
            else:
                time.sleep_ms(100)

# Instantiate and run
central = BLECentral()
central.run()
