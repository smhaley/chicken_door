from machine import Pin

class Indicators:
    def __init__(self, fault, motion, manual):
        self.fault = Pin(fault, Pin.OUT)
        self.motion = Pin(motion, Pin.OUT)
        self.manual = Pin(manual, Pin.OUT)


class Buttons:
    def __init__(self, up_button, down_button, reset_button):
        self.up_button = Pin(up_button, Pin.IN, Pin.PULL_DOWN)
        self.down_button = Pin(down_button, Pin.IN, Pin.PULL_DOWN)
        self.reset_button = Pin(reset_button, Pin.IN, Pin.PULL_DOWN)
        
