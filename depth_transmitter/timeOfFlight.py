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

    def getRawMeasurement(self):
        out = (self.tof.ping() / 1000.0)
        if self.isShortRange:
            out -= 0.025
        return out

    def rolling_average(self):
        return sum(self.rolling_buffer) / len(self.rolling_buffer) if self.rolling_buffer else 0
    
    def getAverageMeasurement(self):
        self.rolling_buffer.append(self.getRawMeasurement())
        if len(self.rolling_buffer) > self.ROLLING_WINDOW_SIZE:
            self.rolling_buffer.pop(0)  # Remove oldest
        return self.rolling_average()
    
    def sendPulse(self):
        print('Pulse!')

    def run_tof(self):
        self.setShortRange()
        self.isShortRange = True
        self.threshold = 0.3  # meters

        # Rolling average buffer params
        self.ROLLING_WINDOW_SIZE = 10
        self.rolling_buffer = []
        
        for i in range(10):
            self.getAverageMeasurement()

        while True:
            try:
                baseline = self.getAverageMeasurement()
                print(f"baseline: {baseline:.3f} m")
                
                upwardFlag = False
                while True:
                    cur_avg = self.getAverageMeasurement()
                    if cur_avg >= baseline + 0.025:
                        break
                    if cur_avg < baseline - 0.01:
                        upwardFlag = True
                        break
                    self.rolling_buffer.clear()
                    time.sleep_ms(100)
                        
                if upwardFlag:
                    print('Detected upward movement')
                    continue

                self.sendPulse()

                if self.isShortRange:
                    if baseline > self.threshold:
                        print("Switching to long range")
                        self.setLongRange()
                        self.isShortRange = False
                        self.rolling_buffer.clear()  # Clear buffer to avoid stale data
                else:
                    if baseline <= self.threshold:
                        print("Switching to short range")
                        self.setShortRange()
                        self.isShortRange = True
                        self.rolling_buffer.clear()

            except Exception as e:
                print("Read error:", e)

            time.sleep_ms(100)

if __name__ == "__main__":
    tof = TOF_Interface()
    tof.run_tof()
