import bluetooth
import struct
import time

IAM = "Transmitter"
BLE_NAME = IAM
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)

SEND_MESSAGES = [
    "EnableOFF DepthOFF",
    "EnableOFF DepthON",
    "EnableON DepthOFF",
    "EnableON DepthON"
]

class BLEPeripheral:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.bt_irq)
        self.conn_handle = None
        self.message_iter = 0

        self._register_services()
        self._advertise()

    def _register_services(self):
        # Combine flags here, not in import
        flags = bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY
        self.tx = (BLE_CHARACTERISTIC_UUID, flags)
        self.svc = (BLE_SVC_UUID, (self.tx,))
        ((self.tx_handle,),) = self.ble.gatts_register_services((self.svc,))

    def _advertise(self):
        name_bytes = bytes(BLE_NAME, 'utf-8')
        adv_payload = bytearray(
            b'\x02\x01\x06' +                            # Flags
            bytes([len(name_bytes) + 1, 0x09]) +         # Complete local name
            name_bytes
        )
        self.ble.gap_advertise(100_000, adv_payload)
        print(f"{BLE_NAME} is now advertising")

    def bt_irq(self, event, data):
        if event == 1:  # _IRQ_CENTRAL_CONNECT
            self.conn_handle, _, _ = data
            print(f"Connected: handle={self.conn_handle}")
        elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
            print("Disconnected")
            self.conn_handle = None
            self._advertise()

    def send_message(self):
        if self.conn_handle is None:
            return

        try:
            msg = SEND_MESSAGES[self.message_iter]
            self.message_iter = (self.message_iter + 1) % len(SEND_MESSAGES)

            print(f"Sending: {msg}")
            self.ble.gatts_write(self.tx_handle, msg.encode('utf-8'))
            self.ble.gatts_notify(self.conn_handle, self.tx_handle)

        except Exception as e:
            print("Error sending message:", e)

    def run(self):
        while True:
            if self.conn_handle is not None:
                self.send_message()
                time.sleep(0.75)
            else:
                time.sleep(0.1)

# Run the peripheral
ble_peripheral = BLEPeripheral()
ble_peripheral.run()
