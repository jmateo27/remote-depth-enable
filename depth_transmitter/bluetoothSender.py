import aioble
import bluetooth
import asyncio
from sys import exit

# Bluetooth parameters
BLE_NAME = "DEPTH_TRANSMITTER"  # You can dynamically change this if you want unique names
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 30000
BLE_WINDOW = 30000

PULSE_LENGTH_S = 0.75


class Bluetooth_Sender:
    def __init__(self, depthPulse, lock):
        self.depthPulse = depthPulse
        self.lock = lock

    def encode_message(self, message):
        """ Encode a message to bytes """
        return message.encode('utf-8')

    async def send_data_task(self, connection, characteristic):
        """ Send data to the connected device """
        while True:
            if not connection:
                print("error - no connection in send data")
                continue

            if not characteristic:
                print("error no characteristic provided in send data")
                continue
            sMessage = ""

            async with self.lock:
                if self.depthPulse:
                    sMessage = "DepthON"
                    
                else:
                    sMessage = "DepthOFF"

            print(f"sending {sMessage}")

            try:
                msg = self.encode_message(sMessage)
                characteristic.write(msg)
                
            except Exception as e:
                print(f"writing error {e}")
                continue

            await asyncio.sleep(PULSE_LENGTH_S) 

    async def run_transmitter_mode(self):
        """ Run the transmitter mode """

        # Set up the Bluetooth service and characteristic
        ble_service = aioble.Service(BLE_SVC_UUID)
        characteristic = aioble.Characteristic(
            ble_service,
            BLE_CHARACTERISTIC_UUID,
            read=True,
            notify=True,
            write=True,
            capture=True,
        )
        aioble.register_services(ble_service)

        print(f"{BLE_NAME} starting to advertise")

        while True:
            async with await aioble.advertise(
                BLE_ADVERTISING_INTERVAL,
                name=BLE_NAME,
                services=[BLE_SVC_UUID],
                appearance=BLE_APPEARANCE) as connection:
                print(f"{BLE_NAME} connected to another device: {connection.device}")

                tasks = [
                    asyncio.create_task(self.send_data_task(connection, characteristic)),
                ]
                await asyncio.gather(*tasks)
                print(f"TRANSMITTER disconnected")
                break

async def pulseTimerTester(depthPulse, lock):
    while True:
        await asyncio.sleep(PULSE_LENGTH_S)
        async with lock:
            depthPulse = not depthPulse

async def mainTest(ble, depthPulse, lock):
    """ Main function """
    while True:
        tasks = [
            asyncio.create_task(ble.run_transmitter_mode()),
            asyncio.create_task(pulseTimerTester(depthPulse, lock))
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    depthPulse = False
    lock = asyncio.Lock()
    ble = Bluetooth_Sender(depthPulse, lock)
    asyncio.run(mainTest(ble, depthPulse, lock))
