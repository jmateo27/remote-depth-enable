import machine
import time

VL53L0X_ADDR = 0x29
VL53L0X_SDA_PIN = 4
VL53L0X_SCL_PIN = 5
MAX_OPERATING_FREQUENCY = 100_000

class VL53L0X:
    def __init__(self, scl_pin, sda_pin, id):
        self.i2c = machine.I2C(id,
                               sda=machine.Pin(sda_pin),
                               scl=machine.Pin(scl_pin),
                               freq=MAX_OPERATING_FREQUENCY)
        if VL53L0X_ADDR not in self.i2c.scan():
            raise RuntimeError("VL53L0X not found on I2C bus.")
        
        self._init_sensor()
        self._set_long_range_mode()

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(VL53L0X_ADDR, reg, bytes([value]))

    def read_reg(self, reg):
        return self.i2c.readfrom_mem(VL53L0X_ADDR, reg, 1)[0]

    def read_reg16(self, reg):
        data = self.i2c.readfrom_mem(VL53L0X_ADDR, reg, 2)
        return (data[0] << 8) | data[1]

    def _init_sensor(self):
        # Basic ST-recommended init sequence
        try:
            self.write_reg(0x88, 0x00)
            self.write_reg(0x80, 0x01)
            self.write_reg(0xFF, 0x01)
            self.write_reg(0x00, 0x00)
            self._stop_variable = self.read_reg(0x91)
            self.write_reg(0x00, 0x01)
            self.write_reg(0xFF, 0x00)
            self.write_reg(0x80, 0x00)
        except:
            raise RuntimeError("Failed VL53L0X static init")

    def _set_long_range_mode(self):
        try:
            self.write_reg(0x50, 0x12)  # PRE_RANGE_CONFIG_VCSEL_PERIOD = 18 PCLKs
            self.write_reg(0x70, 0x0E)  # FINAL_RANGE_CONFIG_VCSEL_PERIOD = 14 PCLKs
            self._write_u16(0x44, int(0.1 * (1 << 7)))  # signal_rate_limit = 0.1 MCPS
            # Optional: increase timing budget
            self._write_u16(0x71, 0x00FE)  # FINAL_RANGE_CONFIG_TIMEOUT_MACROP
        except:
            print("Failed to apply long range mode")

    def _write_u16(self, reg, value):
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        self.i2c.writeto_mem(VL53L0X_ADDR, reg, bytes([high, low]))

    def read_distance(self):
        # Proper one-shot measurement startup sequence
        self.write_reg(0x80, 0x01)
        self.write_reg(0xFF, 0x01)
        self.write_reg(0x00, 0x00)
        self.write_reg(0x91, self._stop_variable)
        self.write_reg(0x00, 0x01)  # SYSRANGE_START = start single shot
        self.write_reg(0xFF, 0x00)
        self.write_reg(0x80, 0x00)

        # Wait for measurement to complete (poll interrupt status)
        start = time.ticks_ms()
        while not (self.read_reg(0x13) & 0x07):
            if time.ticks_diff(time.ticks_ms(), start) > 100:
                raise RuntimeError("Timeout waiting for distance ready")
            time.sleep_ms(5)
            
        distance = self.read_reg16(0x14 + 10)  # RESULT_RANGE_STATUS + 10
        self.write_reg(0x0B, 0x01)  # SYSTEM_INTERRUPT_CLEAR = 0x01
        return distance

# Run the test loop
if __name__ == "__main__":
    tof = VL53L0X(VL53L0X_SCL_PIN, VL53L0X_SDA_PIN, 0)
    while True:
        try:
            reading = tof.read_distance()
            print(f"Distance: {reading} mm")
        except Exception as e:
            print("Error reading distance:", e)
        time.sleep(1)
