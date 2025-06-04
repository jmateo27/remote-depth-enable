import machine
import utime
import ustruct
import asyncio

_IO_TIMEOUT = 100

class VL53L0X:
    def __init__(self, scl_pin, sda_pin, id=0):
        self.i2c = machine.I2C(id, scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
        self.addr = 0x29
        self._started = False

    def _write_register(self, reg, val):
        if isinstance(val, int):
            val = bytes([val])
        self.i2c.writeto_mem(self.addr, reg, val)

    def _read_register(self, reg, length=1):
        return self.i2c.readfrom_mem(self.addr, reg, length)

    def _register(self, reg, val=None, struct=None):
        if val is None:
            data = self._read_register(reg, 2 if struct == '>H' else 1)
            return ustruct.unpack(struct, data)[0] if struct else data[0]
        else:
            if struct:
                val = ustruct.pack(struct, int(val))
            elif isinstance(val, int):
                val = bytes([val])
            self.i2c.writeto_mem(self.addr, reg, val)

    async def init(self):
        # Simplified init for brevity
        self._write_register(0x88, 0x00)
        await asyncio.sleep_ms(10)
        self._write_register(0x80, 0x01)
        await asyncio.sleep_ms(10)

    async def read(self):
        if not self._started:
            self._register(0x00, 0x01)  # Start ranging
            self._started = True

        for _ in range(_IO_TIMEOUT):
            status = self._register(0x13)
            if status & 0x07:
                break
            await asyncio.sleep_ms(1)
        else:
            raise TimeoutError("Timeout waiting for measurement")

        distance = self._register(0x1E + 10, struct='>H')
        self._register(0x0B, 0x01)  # Clear interrupt
        return distance
