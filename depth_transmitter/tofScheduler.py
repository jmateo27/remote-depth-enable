import uasyncio as asyncio
import time

class TOF_Scheduler:
    def __init__(self, shared):
        self.shared = shared

    async def run(self):
        NUM_TOFS = self.shared["num_tofs"]
        STAGGER_MS = 25
        while True:
            for i in range(NUM_TOFS):
                self.shared["tofs_event"][i].set()
                await asyncio.sleep_ms(STAGGER_MS)