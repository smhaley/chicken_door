from ds3231_gen import DS3231
from machine import Pin, PWM, I2C
from dc_motor import DCMotor
from operate import Operate
from sun import Sun
from auxilary import Buttons, Indicators
# settings related to run voltage
run_params = {
    12: {
        'MAX_RUN_TIME': 45,
        'UP_RUN_TIME': 30,
        'REED_BUFFER': 3.0
        },
    14: {
        'MAX_RUN_TIME': 45,
        'UP_RUN_TIME': 30,
        'REED_BUFFER': 3.0
        }
    }
 
class PinConfig:
    motor = {
        "pin1": 15,
        "pin2": 14,
        "enable": 13
    }
    buttons = {
        "up": 28,
        "down": 26, 
        "reset": 27
    }
    indicators = {
        "fault": 16,
        "motion": 17,
        "manual": 18
    }
    reeds = {
        'upper_reed_switch': 'GP18',
        'lower_reed_switch': 'GP19'
    }
    
    rtc = {
        'scl': 9,
        'sda': 8
    }
    
    
class LocationConfig:
    lat = 42.2293
    lon = -72.7301
    time_offset = -5
    


if __name__ == "__main__":
    
    pins = PinConfig()
    location = LocationConfig()

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
    
    params = run_params[14]
    
    op = Operate(dc_motor, buttons, indicators, rtc, pins.reeds['upper_reed_switch'], pins.reeds['lower_reed_switch'], sun, params['REED_BUFFER'], params['UP_RUN_TIME'], params['MAX_RUN_TIME'])
    op.engage_door()





   
