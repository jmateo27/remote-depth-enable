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

class Bluetooth_Transmitter:
    def __init__(self, depthPulse, mutex):
        self.depthPulse = depthPulse
        self.mutex = mutex

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
            
            # Determine the message depending on the shared variable
            sMessage = ""
            async with self.mutex:
                if self.depthPulse:
                    sMessage = "DepthON"
                else:
                    sMessage = "DepthOFF"

            print(f'Sending message: {sMessage}')
            
            try:
                msg = self.encode_message(sMessage)
                characteristic.write(msg)
                
            except Exception as e:
                print(f"writing error {e}")
                continue

            await asyncio.sleep(DEPTH_PULSE_LENGTH_S)

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
                print(f"{BLE_NAME} disconnected")
                break

async def depthPulseTester(depthPulse, mutex):
    while True:
        await asyncio.sleep(DEPTH_PULSE_LENGTH_S)
        async with mutex:
            depthPulse = not depthPulse
        
async def main():
    """ Main function """
    depthPulse = False
    mutex = asyncio.Lock()
    bt_transmitter = Bluetooth_Transmitter(depthPulse, mutex)
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(depthPulseTester(depthPulse, mutex))
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())
