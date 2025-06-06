import aioble
import bluetooth
import asyncio
from sys import exit

# Bluetooth parameters
BLE_NAME = "TRANSMITTER"  # You can dynamically change this if you want unique names
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 30000
BLE_WINDOW = 30000

DEPTH_PULSE_LENGTH_S = 0.75

async def depthPulseTester(shared, mutex):
    while True:
        await asyncio.sleep(DEPTH_PULSE_LENGTH_S)
        async with mutex:
            shared["depthPulse"] = not shared["depthPulse"]
            print(f"[Tester] depthPulse is now {shared['depthPulse']}")

class Bluetooth_Transmitter:
    def __init__(self, shared, mutex):
        self.shared = shared
        self.mutex = mutex

    def encode_message(self, message):
        return message.encode('utf-8')

    async def send_data_task(self, connection, characteristic):
        while True:
            if not connection:
                print("error - no connection in send data")
                continue

            if not characteristic:
                print("error no characteristic provided in send data")
                continue
            
            async with self.mutex:
                depth = self.shared["depthPulse"]
                sMessage = "DepthON" if depth else "DepthOFF"

            print(f'Sending message: {sMessage}')

            try:
                msg = self.encode_message(sMessage)
                characteristic.write(msg)
            except Exception as e:
                print(f"writing error {e}")
                continue

            await asyncio.sleep(DEPTH_PULSE_LENGTH_S)

# in main
async def main():
    shared = {"depthPulse": False}
    mutex = asyncio.Lock()
    bt_transmitter = Bluetooth_Transmitter(shared, mutex)
    
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(depthPulseTester(shared, mutex))
        ]
        await asyncio.gather(*tasks)
