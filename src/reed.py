from machine import Pin, PWM
import time

class ReedSwitchStatus:
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

class ReedSwitchControl:
    def __init__(self, pin):
        self.reed_switch = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.status = self.get_status()
        
    def set_status(self, status):
        if (status == self.get_status()):
            self.status = status
        
    def get_status(self):
        switch_state = self.reed_switch.value()
        if switch_state == 0:  # Reed switch is closed (magnet detected)
            return ReedSwitchStatus.CLOSED
        else:  # Reed switch is open
            return ReedSwitchStatus.OPEN


        
