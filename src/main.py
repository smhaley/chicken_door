from ds3231_gen import DS3231
from machine import Pin, PWM, I2C
from dc_motor import DCMotor
from operate import Operate
from sun import Sun


if __name__ == "__main__":

    lat = 42.2293
    lon = -72.7301
    coords = {'longitude' : lon, 'latitude' : lat}
    sun = Sun(coords, -4)

    rtc_i2c = I2C(0, scl=Pin(17), sda=Pin(16))
    rtc = DS3231(rtc_i2c)

    frequency = 1000
    pin1 = Pin(3, Pin.OUT)
    pin2 = Pin(4, Pin.OUT)
    enable = PWM(Pin(2), frequency)
    dc_motor = DCMotor(pin1, pin2, enable, 15000, 65535)


    upper_reed_switch_pin = 'GP18'
    lower_reed_switch_pin = 'GP19'
    
    up_button = Pin(15, Pin.IN, Pin.PULL_DOWN)
    down_button = Pin(14, Pin.IN, Pin.PULL_DOWN)
    reset_button = Pin(13, Pin.IN, Pin.PULL_DOWN)

    op = Operate(dc_motor, up_button, down_button, reset_button, rtc, upper_reed_switch_pin, lower_reed_switch_pin, sun, 100)
    op.engage_door()






