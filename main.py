from lab1 import Lab1
import aioble
import bluetooth
import asyncio
import struct
from sys import exit

# Define UUIDs for the service and characteristic
_SERVICE_UUID = bluetooth.UUID(0x1848)
_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)

# IAM = "Central" # Change to 'Peripheral' or 'Central'
IAM = "Peripheral"

if IAM not in ['Peripheral','Central']:
    print("IAM must be either Peripheral or Central")
    exit()

if IAM == "Central":
    IAM_SENDING_TO = "Peripheral"
else:
    IAM_SENDING_TO = "Central"

MESSAGE = f"Hello from {IAM}!"

# Bluetooth parameters
BLE_NAME = f"{IAM}"  # You can dynamically change this if you want unique names
BLE_SVC_UUID = bluetooth.UUID(0x181A)
BLE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2A6E)
BLE_APPEARANCE = 0x0300
BLE_ADVERTISING_INTERVAL = 2000
BLE_SCAN_LENGTH = 5000
BLE_INTERVAL = 30000
BLE_WINDOW = 30000

# state variables
message_count = 0

def decode_message(message):
    """ Decode a message from bytes """
    return message.decode('utf-8')

async def receive_data_task(characteristic):
    """ Receive data from the connected device """
    global message_count
    while True:
        try:
            data = await characteristic.read()
            rMessage = decode_message(data) #rMeassage means Received Message
            
            process = Lab1()
            
            if rMessage == "EnableON DepthON":
                process.setDepthHigh()
                process.setEnableHigh()
            else if rMessage == "EnableOFF DepthON"
                process.setDepthHigh()
                process.setEnableLow()
            else if rMessage == "EnableON DepthOFF"
                process.setDepthLow()
                process.setEnableHigh()
            else if rMessage == "EnableOFF DepthOFF"
                process.setDepthLow()
                process.setEnableLow()
            else
                print("Reveiced Message did not match any of the four on/off possibilities. Error in communciation")
                break

            if data:
                print(f"{IAM} received: {rMessage}, count: {message_count} \n{process.enable.value} {process.depth.value}")
                await characteristic.write(encode_message("Got it"))
                await asyncio.sleep(0.5)

            message_count += 1

        except asyncio.TimeoutError:
            print("Timeout waiting for data in {ble_name}.")
            break
        except Exception as e:
            print(f"Error receiving data: {e}")
            break

async def run_peripheral_mode():
    """ Run the peripheral mode """

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
                asyncio.create_task(receive_data_task(connection, characteristic)),
            ]
            await asyncio.gather(*tasks)
            print(f"{IAM} disconnected")
            break

async def ble_scan():
    """ Scan for a BLE device with the matching service UUID """

    print(f"Scanning for BLE Beacon named {BLE_NAME}...")

    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.name() == IAM_SENDING_TO and BLE_SVC_UUID in result.services():
                print(f"found {result.name()} with service uuid {BLE_SVC_UUID}")
                return result
    return None

async def main():
    """ Main function """
    while True:
        tasks = [
            asyncio.create_task(run_peripheral_mode()),
        ]

        await asyncio.gather(*tasks)

asyncio.run(main())

