import machine # type: ignore
import time

# VL53L0X I2C address 
VL53L0X_ADDR = 0x29

# Max Frequency
MAX_OPERATING_FREQUENCY = 400000

class VL53L0X:
    def __init__ (self, scl_pin, sda_pin, id):
        self.i2c = machine.I2C(id,
                                sda=machine.Pin(sda_pin),
                                scl=machine.Pin(scl_pin),
                                freq=MAX_OPERATING_FREQUENCY)
        self.init_sensor()

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(VL53L0X_ADDR, reg, bytes([value]))

    def read_reg(self, reg):
        return self.i2c.readfrom_mem(VL53L0X_ADDR, reg, 1)[0]
    
    def init_sensor(self):
        # Basic initialization sequence (simplified)
        try: 
            self.write_reg(0x88, 0x00)
            self.write_reg(0x80, 0x01)
            self.write_reg(0xFF, 0x01)
            self.write_reg(0x00, 0x00)
            self.write_reg(0x91, 0x3c)
            self.write_reg(0xFF, 0x00)
            self.write_reg(0x80, 0x00)
        except:
            raise RuntimeError("Failed to initialize VL53L0X")
        
    def read_distance(self):
        self.write_reg(0x00, 0x01) #start single measurement
        time.sleep_ms(50)
        dist_bytes = self.i2c.readfrom_mem(self.addr, 0x14, 2)
        return (dist_bytes[0]<< 8) | dist_bytes[1]

if __name__ == "__main__":
    tof = VL53L0X(sda_pin=14, scl_pin=15, id=0)
    while True:
        reading = tof.read_distance()
        print(reading)
        time.sleep(1)