import asyncio
from timeOfFlight import TOF_Interface
from bluetoothTransmitter import Bluetooth_Transmitter

async def main():
    """ Main function """
    shared = {"depthPulse": False}
    mutex = asyncio.Lock()
    bt_transmitter = Bluetooth_Transmitter(shared, mutex)
    tof = TOF_Interface(shared, mutex)
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(tof.run_tof())
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())