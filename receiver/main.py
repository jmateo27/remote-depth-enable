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
FAST_PULSE_OFF_MS = 20

ON = 0
# OFF = 0
MESSAGES = ["O"]

def decode_message(message):
    """ Decode a message from bytes """
    return message.decode('utf-8')

def messageIsValid(message):
    return True if message in MESSAGES else False

async def receive_data_task(characteristic):
    """ Receive data from the connected device """
    process = Lab1()
    curr_msg = ""
    timer_start = ticks_ms()
    count = 0

    try:
        await characteristic.subscribe()  # Start receiving notifications

        while True:
            try:
                # Wait for new notification, max 200ms
                data = await asyncio.wait_for(characteristic.notified(), timeout=0.2)
                curr_msg = decode_message(data)

                if not messageIsValid(curr_msg):
                    continue

                print("Received:", curr_msg)

            except asyncio.TimeoutError:
                # No data received within 200ms
                curr_msg = None

            depthHigh = process.depth.value() == 1

            # If depth is high, we may want to lower it based on timeout or OFF
            if depthHigh and (
                ticks_diff(ticks_ms(), timer_start) >= DEPTH_INTERVAL_ON_MS
            ):
                print("Depth low.")
                process.setDepthLow()
            # If depth is low, raise it if message says ON
            elif not depthHigh and curr_msg == MESSAGES[ON]:
                print(f"Depth high(1) {count}!")
                count += 1
                process.setDepthHigh()
                timer_start = ticks_ms()
            elif depthHigh:
                # Set depth low for a few ms, then back high
                process.setDepthLow()
                await asyncio.sleep_ms(FAST_PULSE_OFF_MS)
                print(f"Depth high(2) {count}!")
                count += 1
                process.setDepthHigh()
                timer_start = ticks_ms()
            

    except Exception as e:
        print(f"Error receiving data: {e}")
        
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

