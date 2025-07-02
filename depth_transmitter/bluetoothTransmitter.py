import aioble
import bluetooth
import uasyncio as asyncio
from sys import exit
import time

# Bluetooth parameters
BLE_NAME = "TRANSMITTER"  # You can dynamically change this if you want unique names
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 10000
BLE_WINDOW = 10000

DEPTH_PERIOD_MS = 50
DEPTH_PULSE_LENGTH_MS = 25
DEPTH_OFF_MS = DEPTH_PERIOD_MS - DEPTH_PULSE_LENGTH_MS

ON = 1
OFF = 0
MESSAGES = ["DepthOFF", "DepthON"]

class Bluetooth_Transmitter:
    def __init__(self, event):
        self.event = event

    def encode_message(self, message):
        """ Encode a message to bytes """
        return message.encode('utf-8')

    async def send_data_task(self, connection, characteristic):
        """ Send data to the connected device """
        while True:

            # Checks to see if able to send data at all
            if not connection:
                print("error - no connection in send data")
                continue

            if not characteristic:
                print("error no characteristic provided in send data")
                continue

            # Idle until event is set
            await self.event.wait()
            self.event.clear() # Un-set the event for future use
                
            # ON for 25 ms (fixed), OFF for 25 ms (at least)
            try:
                t0 = time.ticks_ms()
                await characteristic.notify(connection, self.encode_message(MESSAGES[ON]))
                print(f"Took {time.ticks_ms() - t0} ms to notify ON (1)")
            except Exception as e:
                print(f"Took {time.ticks_ms() - t0} ms to notify ON (2)")
                
            await asyncio.sleep_ms(DEPTH_PULSE_LENGTH_MS)
            
            try:
                t0 = time.ticks_ms()
                await characteristic.notify(connection, self.encode_message(MESSAGES[OFF]))
                print(f"Took {time.ticks_ms() - t0} ms to notify OFF (1)")
            except Exception as e:
                print(f"Took {time.ticks_ms() - t0} ms to notify OFF (2)")
            
            await asyncio.sleep_ms(DEPTH_OFF_MS)

    async def run_transmitter_mode(self):
        """ Run the transmitter mode """

        # Set up the Bluetooth service and characteristic
        ble_service = aioble.Service(BLE_SVC_UUID)
        characteristic = aioble.Characteristic(
            ble_service,
            BLE_CHARACTERISTIC_UUID,
            read=False,
            notify=True,
            write=False,
            capture=False,
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

async def depthPulseTester(shared, mutex):
    while True:
        await asyncio.sleep(DEPTH_PULSE_LENGTH_S)
        async with mutex:
            shared["depthPulse"] = not shared["depthPulse"]
        
async def main():
    """ Main function """
    shared = {"depthPulse": False}
    mutex = asyncio.Lock()
    bt_transmitter = Bluetooth_Transmitter(shared, mutex)
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(depthPulseTester(shared, mutex))
        ]
        await asyncio.gather(*tasks)

# asyncio.run(main())
