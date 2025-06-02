import machine
import time

# Defining pin numbers for depth and enable signals
DEPTHSIGNAL_PIN = 27
ENABLESIGNAL_PIN = 26
SWITCHENABLESIGNAL_PIN = 21
SWITCHDEPTHSIGNAL_PIN = 20
MEASUREMENTLATENCY_MS = 5


# Lab1 Set pin for depth to show in eBaux
class Lab1:
    def __init__(self):
        self.depth = machine.Pin(DEPTHSIGNAL_PIN, machine.Pin.OUT, value=0)
        self.enable = machine.Pin(ENABLESIGNAL_PIN, machine.Pin.OUT, value=0)
        self.switchEnable = machine.Pin(SWITCHENABLESIGNAL_PIN, machine.Pin.IN)
        self.switchDepth = machine.Pin(SWITCHDEPTHSIGNAL_PIN, machine.Pin.IN)
        
    def setDepthHigh(self):
        self.depth.value(1)
    
    def setDepthLow(self):
        self.depth.value(0)
        
    def setEnableHigh(self):
        self.enable.value(1)
    
    def setEnableLow(self):
        self.enable.value(0)
        
    def getSwitchEnable(self):
        return self.switchEnable.value()
    
    def getSwitchDepth(self):
        print(self.switchDepth.value())
        return self.switchDepth.value()
    
    def main(self):
        while True:
            if self.getSwitchEnable() == 1:
                self.setEnableHigh()
            else:
                self.setEnableLow()
                
            if self.getSwitchDepth() == 1:
                self.setDepthHigh()
            else:
                self.setDepthLow()
            
            time.sleep_ms(MEASUREMENTLATENCY_MS)
            
if __name__ == "__main__":
    process = Lab1()
    process.main()
                

    
    
        
    
        
        
        
    
    