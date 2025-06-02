import aioble
import bluetooth
import asyncio
from sys import exit

IAM = "Transmitter"

if IAM not in ['Receiver','Transmitter']:
    print("IAM must be either Receiver or Transmitter")
    exit()

if IAM == "Receiver":
    IAM_SENDING_TO = "Transmitter"
else:
    IAM_SENDING_TO = "Receiver"

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

def encode_message(message):
    """ Encode a message to bytes """
    return message.encode('utf-8')

def decode_message(message):
    """ Decode a message from bytes """
    return message.decode('utf-8')

async def send_data_task(connection, characteristic):
    """ Send data to the connected device """
    global message_count
    while True:
        if not connection:
            print("error - no connection in send data")
            continue

        if not characteristic:
            print("error no characteristic provided in send data")
            continue

        message = f"{MESSAGE} {message_count}"
        message_count +=1
        print(f"sending {message}")

        try:
            msg = encode_message(message)
            characteristic.write(msg)

            await asyncio.sleep(0.5)
            response = decode_message(characteristic.read())

            print(f"{IAM} sent: {message}, response {response}")
        except Exception as e:
            print(f"writing error {e}")
            continue

        await asyncio.sleep(0.5)

async def run_transmitter_mode():
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
                asyncio.create_task(send_data_task(connection, characteristic)),
            ]
            await asyncio.gather(*tasks)
            print(f"{IAM} disconnected")
            break

async def main():
    """ Main function """
    while True:
        if IAM == "Central":
            tasks = [
                asyncio.create_task(run_central_mode()),
            ]
        else:
            tasks = [
                asyncio.create_task(run_transmitter_mode()),
            ]

        await asyncio.gather(*tasks)

asyncio.run(main())
