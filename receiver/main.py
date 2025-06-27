from lab1 import Lab1
import aioble
import bluetooth
import asyncio
from sys import exit
from time import ticks_ms, ticks_diff

# Bluetooth parameters
BLE_NAME = "RECEIVER"
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 10000
BLE_WINDOW = 10000

DEPTH_INTERVAL_ON_MS = 200
POLLING_LATENCY_MS = 20

ON = 1
OFF = 0
MESSAGES = ["DepthOFF", "DepthON"]

def decode_message(message):
    """ Decode a message from bytes """
    return message.decode('utf-8')

def messageIsValid(message):
    return True if message in MESSAGES else False

async def receive_data_task(characteristic):
    """ Receive data from the connected device """
    # Initialize some variables needed for later
    process = Lab1()
    curr_msg = "DepthOFF"
    timer_start = ticks_ms()
    
    count = 0
    while True:
        try:
            # Start to time for elapsed time
            t0 = ticks_ms()

            # Set prev_msg for later checking of state
            prev_msg = curr_msg

            # Get what is in the characteristic and verify if valid message
            async for data in characteristic.notifications():
                curr_msg = decode_message(data)
                if not messageIsValid(curr_msg):
                    continue
                print(ticks_ms() - t0)
                # Check whether depth is high or low currently
                depthHigh = process.depth.value() == 1

                
                if depthHigh and ( # Follow only if depth is currently high
                    (ticks_diff(ticks_ms(), timer_start) >= DEPTH_INTERVAL_ON_MS)   # Set depth low if it's been 200 ms
                    or (prev_msg == MESSAGES[OFF] and curr_msg == MESSAGES[ON])     # Set depth low if the previous message said OFF, but is now ON  
                ):
                    print("Depth low.")
                    process.setDepthLow()
                elif not depthHigh and (curr_msg == MESSAGES[ON]):
                    print(f"Depth high {count}!")
                    count = count + 1
                    # Set depth high if depth is low and messages says ON
                    process.setDepthHigh()
                    # Start the timer for limiting depth pulse to 200 ms
                    timer_start = ticks_ms()
            
        except asyncio.TimeoutError:
            print("Timeout waiting for data in {ble_name}.")
            break
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

async def run_receiver_mode():
    """ Run the receiver mode """

    # Start scanning for a device with the matching service UUID
    while True:
        device = await ble_scan()

        if device is None:
            continue
        print(f"device is: {device}, name is {device.name()}")

        try:
            print(f"Connecting to {device.name()}")
            connection = await device.device.connect()

        except asyncio.TimeoutError:
            print("Timeout during connection")
            continue

        print(f"RECEIVER connected to {connection}")

        # Discover services
        async with connection:
            try:
                service = await connection.service(BLE_SVC_UUID)
                characteristic = await service.characteristic(BLE_CHARACTERISTIC_UUID)
            except (asyncio.TimeoutError, AttributeError):
                print("Timed out discovering services/characteristics")
                continue
            except Exception as e:
                print(f"Error discovering services {e}")
                await connection.disconnect()
                continue

            tasks = [
                asyncio.create_task(receive_data_task(characteristic)),
            ]
            await asyncio.gather(*tasks)

            await connection.disconnected()
            print(f"{BLE_NAME} disconnected from {device.name()}")
            break

async def ble_scan():
    """ Scan for a BLE device with the matching service UUID """

    print(f"Scanning for BLE Beacon named {BLE_NAME}...")

    async with aioble.scan(5000, interval_us=10000, window_us=10000, active=True) as scanner:
        async for result in scanner:
            try:
                name = result.name()
            except UnicodeError:
                name = None
            if name == "TRANSMITTER" and BLE_SVC_UUID in result.services():
                print(f"found {name} with service uuid {BLE_SVC_UUID}")
                return result
    return None

async def main():
    """ Main function """
    while True:
        tasks = [
            asyncio.create_task(run_receiver_mode()),
        ]

        await asyncio.gather(*tasks)

asyncio.run(main())

