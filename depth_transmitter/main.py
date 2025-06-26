import uasyncio as asyncio
from timeOfFlight import TOF_Interface
from bluetoothTransmitter import Bluetooth_Transmitter

async def main():
    """ Main function """
    event = asyncio.Event()
    bt_transmitter = Bluetooth_Transmitter(event)
    tof = TOF_Interface(event)
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(tof.run_tof())
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())