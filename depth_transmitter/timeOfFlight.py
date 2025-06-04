import time
from machine import Pin, I2C
from vl53l0x import VL53L0X
import asyncio

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

class TOF_Interface:
    def __init__(self):
        self.i2c = I2C(id=I2C_ID, sda=I2C_SDA_PIN, scl=I2C_SCL_PIN)
        self.tof = VL53L0X(self.i2c)
        self.tof.set_measurement_timing_budget(40000)

    def setShortRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 12)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 8)

    def setLongRange(self):
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[0], 18)
        self.tof.set_Vcsel_pulse_period(self.tof.vcsel_period_type[1], 14)

    def rolling_average(buffer):
        return sum(buffer) / len(buffer) if buffer else 0
    
    async def run_tof(self):
        self.setShortRange()
        self.isShortRange = True
        self.threshold = 0.3  # meters

        # Rolling average buffer params
        self.ROLLING_WINDOW_SIZE = 10
        self.rolling_buffer = []

        while True:
            try:
                raw_measurement = (await self.tof.ping()) / 1000.0  # Convert mm to meters and offset
                if isShortRange:
                    raw_measurement -= 0.025
                # Add new measurement to buffer
                self.rolling_buffer.append(raw_measurement)
                if len(self.rolling_buffer) > self.ROLLING_WINDOW_SIZE:
                    self.rolling_buffer.pop(0)  # Remove oldest

                avg_measurement = self.rolling_average(self.rolling_buffer)

                print(f"Raw: {raw_measurement:.3f} m, Avg: {avg_measurement:.3f} m")

                if isShortRange:
                    if avg_measurement > self.threshold:
                        print("Switching to long range")
                        self.setLongRange()
                        isShortRange = False
                        self.rolling_buffer.clear()  # Clear buffer to avoid stale data
                else:
                    if avg_measurement <= self.threshold:
                        print("Switching to short range")
                        self.setShortRange()
                        isShortRange = True
                        self.rolling_buffer.clear()

            except Exception as e:
                print("Read error:", e)

            time.sleep_ms(100)

async def main():
    tof = await TOF_Interface()
    while True:
        tasks = [
            asyncio.create_task(tof.run_tof()),
        ]

        await asyncio.gather(*tasks)
    
    

if __name__ == "__main__":
    asyncio.run(main())
