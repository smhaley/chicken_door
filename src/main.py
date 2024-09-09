from ds3231_gen import DS3231
from machine import Pin, PWM, I2C
from dc_motor import DCMotor
from operate import Operate
from sun import Sun

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


if __name__ == "__main__":

    lat = 42.2293
    lon = -72.7301
    time_offset = -5
    
    coords = {'longitude' : lon, 'latitude' : lat}
    sun = Sun(coords, time_offset)

    rtc_i2c = I2C(0, scl=Pin(9), sda=Pin(8))
    rtc = DS3231(rtc_i2c)

    frequency = 1000
    pin1 = Pin(15, Pin.OUT)
    pin2 = Pin(14, Pin.OUT)
    enable = PWM(Pin(13), frequency)
    dc_motor = DCMotor(pin1, pin2, enable, 15000, 65535)


    upper_reed_switch_pin = 'GP18'
    lower_reed_switch_pin = 'GP19'
    
    up_button = Pin(28, Pin.IN, Pin.PULL_DOWN)
    down_button = Pin(26, Pin.IN, Pin.PULL_DOWN)
    reset_button = Pin(27, Pin.IN, Pin.PULL_DOWN)
    
    params = run_params[14]
    
    op = Operate(dc_motor, up_button, down_button, reset_button, rtc, upper_reed_switch_pin, lower_reed_switch_pin, sun, params['REED_BUFFER'], params['UP_RUN_TIME'], params['MAX_RUN_TIME'])
    op.engage_door()





   
