import uasyncio as asyncio
from timeOfFlight import TOF_Interface
from bluetoothTransmitter import Bluetooth_Transmitter
from pulser import Pulser
from tofScheduler import TOF_Scheduler

NUM_TOFS = 2

async def main():
    """ Main function """
    shared = {
        "pulse_event": asyncio.Event(),
        "new_reading": asyncio.Event(),
        "num_tofs": NUM_TOFS,
        "tofs_event": [asyncio.Event() for _ in range(NUM_TOFS)],
        "reading": None
    }
    
    bt_transmitter = Bluetooth_Transmitter(shared)
    tofs = [TOF_Interface(shared, i) for i in range(NUM_TOFS)]
    pulser = Pulser(shared)
    tof_scheduler = TOF_Scheduler(shared)

    while True:
        tasks = [
            asyncio.create_task(bt_transmitter.run_transmitter_mode()),
            asyncio.create_task(pulser.run()),
            asyncio.create_task(tof_scheduler.run())
        ]
        tasks += [asyncio.create_task(tof.run_tof()) for tof in tofs]

        await asyncio.gather(*tasks)

asyncio.run(main())