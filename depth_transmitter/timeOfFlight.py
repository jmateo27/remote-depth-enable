import asyncio
from machine import Pin, I2C
from vl53l0x import VL53L0X
from time import ticks_ms, ticks_diff
import uasyncio as asyncio

I2C0_ID = 0
I2C1_ID = 1
I2C_SDA_PINS = [4, 18]
I2C_SCL_PINS = [5, 19]

MAX_MEASUREMENT_M = 2.5

class TOF_Interface:
    def __init__(self, shared, i2c_id):
        self.id = i2c_id
        self.shared = shared
        self.i2c = I2C(id=i2c_id, sda=Pin(I2C_SDA_PINS[i2c_id]), scl=Pin(I2C_SCL_PINS[i2c_id]))
        self.tof = VL53L0X(self.i2c)
        self.tof.set_measurement_timing_budget(40000)
        self.ROLLING_WINDOW_SIZE = 10
        self.rolling_buffer = []
        self.isShortRange = True
        self.RANGE_THRESHOLD = 0.3
        self.MEASUREMENT_BUFFER_MS = 20
        self.SAMPLING_BUFFER_MS = 40
        print("Finished init")

    def setShortRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 12)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 8)

    def setLongRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 18)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 14)
        
    async def getRawMeasurement(self):
        out = (await self.tof.ping() / 1000.0)
#         if self.isShortRange:
#             out -= 0.025
        if self.id == 1:
            out += 0.005
        return out
            
    async def run_tof(self):
        if self.id == I2C1_ID:
            await asyncio.sleep_ms(18)

        self.setShortRange()
        self.isShortRange = True
        
        await asyncio.sleep(1)
        await self.getRawMeasurement()
        baseline = await self.getRawMeasurement()
        print(f"Baseline: {(baseline*100):.3f} cm")

        while True:
            measurement = await self.getRawMeasurement()

            if measurement < MAX_MEASUREMENT_M:
#                 print(f"Valid measurement: {measurement*100}cm, sensor {self.id}")
                self.shared["reading"] = measurement - baseline
                self.shared["new_reading"].set()

                if self.isShortRange:
                    if measurement > self.RANGE_THRESHOLD:
#                         print("Switching to long range")
                        self.setLongRange()
                        self.isShortRange = False
                        self.rolling_buffer.clear()
                else:
                    if measurement <= self.RANGE_THRESHOLD:
#                         print("Switching to short range")
                        self.setShortRange()
                        self.isShortRange = True
                        self.rolling_buffer.clear()

    async def test_tof(self):
        print("Testing")
        self.setShortRange()
        self.isShortRange = True
        
        await asyncio.sleep(1)
        await self.getRawMeasurement()
        baseline = await self.getRawMeasurement()
        print(f"Baseline: {(baseline*100):.3f} cm")
        
        while True:
            measurement = await self.getRawMeasurement()
            print(f"{measurement*100} cm")
            
            if self.isShortRange:
                if measurement > self.RANGE_THRESHOLD:
                    print("Switching to long range")
                    self.setLongRange()
                    self.isShortRange = False
                    self.rolling_buffer.clear()
            else:
                if measurement <= self.RANGE_THRESHOLD:
                    print("Switching to short range")
                    self.setShortRange()
                    self.isShortRange = True
                    self.rolling_buffer.clear()
                    
if __name__ == "__main__":
    tof = TOF_Interface(None, 1)
    asyncio.run(tof.test_tof())
