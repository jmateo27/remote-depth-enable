import uasyncio as asyncio
from timeOfFlight import TOF_Interface
from bluetoothTransmitter import Bluetooth_Transmitter

async def main():
    """ Main function """
    shared = {
        "event": asyncio.Event(),
        "pulse_source": None
    }
    bt_transmitter = Bluetooth_Transmitter(shared)
    tof1 = TOF_Interface(shared, 0)
    tof2 = TOF_Interface(shared, 1)
    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(tof1.run_tof()),
            asyncio.create_task(tof2.run_tof())
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())