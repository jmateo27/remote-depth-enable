import uasyncio as asyncio
import time

STEP_SIZE_CM = 2.5
# STEP_SIZE_CM = 1.0
M_PER_CM = 0.01
CM_PER_M = 100

STEP_TOLERANCE_CM = STEP_SIZE_CM * 0.15
STATIONARY_TOLERANCE_CM = STEP_SIZE_CM * 0.7
MAX_MEASUREMENT_M = 2.5

class Pulser:
    def __init__(self, shared):
        self.shared = shared

    async def run(self):
        prev_reading = -1
        count = 0
        t0 = time.ticks_ms()
        while True:
            
            await self.shared["new_reading"].wait()
            
            self.shared["new_reading"].clear() # Un-set the event for future use
            reading = self.shared["reading"]

            if ((	((abs(reading * CM_PER_M) % STEP_SIZE_CM) < (STEP_TOLERANCE_CM))
                or  ((abs(reading * CM_PER_M) % STEP_SIZE_CM) > (STEP_SIZE_CM - STEP_TOLERANCE_CM)))
                and (abs((reading - prev_reading)) > (STATIONARY_TOLERANCE_CM * M_PER_CM))
            ):      
                self.shared["pulse_event"].set()
                prev_reading = reading
                print(f"PULSE#{count}")
                print(f"{time.ticks_ms() - t0} since last pulse")
                t0 = time.ticks_ms()
                count += 1
            