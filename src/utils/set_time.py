from ds3231_gen import DS3231
from machine import Pin, I2C
import time


def set_machine_time(i2c):
    rtc = DS3231(i2c)

    pre = list(time.localtime())
    pre[6] = 0
    pre[3] = pre[3] - 1 # remove if in standard time
    fixed = tuple(pre)
    est = time.localtime(time.mktime(fixed))


    rtc.set_time(est)

    print(f"rtc time: {rtc.get_time()}, time local: {time.localtime()}")
    

i2c = I2C(0, scl=Pin(17), sda=Pin(16))
set_machine_time(i2c)