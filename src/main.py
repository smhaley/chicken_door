from ds3231_gen import DS3231
from machine import Pin, PWM, I2C
from dc_motor import DCMotor
from operate import Operate
from sun import Sun
from auxilary import Buttons, Indicators
from settings import PinConfig, RunParameters, LocationConfig


if __name__ == "__main__":
    
    pins = PinConfig()
    location = LocationConfig()
    params = RunParameters()

    coords = {'longitude' : location.lon, 'latitude' : location.lat}
    sun = Sun(coords, location.time_offset)

    rtc_i2c = I2C(0, scl=Pin(pins.rtc['scl']), sda=Pin(pins.rtc['sda']))
    rtc = DS3231(rtc_i2c)

    frequency = 1000
    pin1 = Pin(pins.motor['pin1'], Pin.OUT)
    pin2 = Pin(pins.motor['pin2'], Pin.OUT)
    enable = PWM(Pin(13), frequency)
    dc_motor = DCMotor(pin1, pin2, enable, 15000, 65535)

    
    buttons = Buttons(pins.buttons['up'], pins.buttons['down'], pins.buttons['reset'])
    indicators = Indicators(pins.indicators['fault'], pins.indicators['motion'], pins.indicators['manual'])
    
    
    op = Operate(
        dc_motor, 
        buttons, 
        indicators, 
        rtc, 
        pins.reeds, 
        sun, 
        params.twelve
        )
    op.engage_door()





   
