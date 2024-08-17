from ds3231_gen import DS3231
from machine import Pin, PWM, I2C
from time import sleep, time
from dc_motor import DCMotor
from reed import ReedSwitchStatus, ReedSwitchControl
from sun import Sun

class Operate:
    
    DOOR_UP = 'up'
    DOOR_DOWN = 'down'
    
    RESET = 'reset'
    
    DOOR_OPEN = 'open'
    DOOR_CLOSED = 'closed'
    DOOR_MOTION = 'motion'
    
    
    def __init__(self, dc_motor, up_button, down_button, reset_button, rtc, upper_reed_switch_pin, lower_reed_switch_pin, sun, max_run_time = 40):
        #self.bottom_switch = bottom_switch
        
        self.dc_motor = dc_motor
        self.up_button = up_button
        self.down_button = down_button
        self.reset_button = reset_button
        self.rtc = rtc
        self.upper_reed = ReedSwitchControl(upper_reed_switch_pin)
        self.lower_reed = ReedSwitchControl(lower_reed_switch_pin)
        self.sun = sun
        self.status = None
        self.fault = 0
        self.day = None
        self.up_time = None
        self.down_time = None
        self.max_run_time = max_run_time
        
        dc_motor.stop()
        self.init()
        
    def add_fault(self):
        self.fault += 1
        dc_motor.stop()
    

    def set_door_status(self):
        upper_status = self.upper_reed.get_status()
        lower_status = self.lower_reed.get_status()
        
        print(f"upper_status: {upper_status}, lower_status: {lower_status}")
        
        if upper_status == ReedSwitchStatus.OPEN and lower_status == ReedSwitchStatus.OPEN:
            self.status =  Operate.DOOR_MOTION
            return
            
        elif upper_status == ReedSwitchStatus.CLOSED and lower_status == ReedSwitchStatus.OPEN:
            self.status = Operate.DOOR_OPEN
            return 
        elif upper_status == ReedSwitchStatus.OPEN and lower_status == ReedSwitchStatus.CLOSED:
            self.status = Operate.DOOR_CLOSED
            return 
            
        else:
            self.add_fault()
            
 
    def _get_day(self, time_tuple):
        return time_tuple[2]
        
    def _get_up_down_hours(self, time_tuple):
        sun_times = sun.getSunTimes(time_tuple)
        sun_rise = sun_times["sunrise"]["decimal"]
        sun_set = sun_times["sunset"]["decimal"]
        return {"up": sun_rise, "down": sun_set}
    
    def _get_hour(self, time):
        hour, mins = time[3:5]
        return round(hour+mins/60,4)
    
    def _initialize_times(self):
        today = self.rtc.get_time()
        self.day = self._get_day(today)
        times = self._get_up_down_hours(today)
        self.up_time = times["up"]
        self.down_time = times["down"]
        
    def operate_door(self, direction):
        
        ticks = 0
        
        while self.status == Operate.DOOR_MOTION:
                        
            upper_status = self.upper_reed.get_status()
            lower_status = self.lower_reed.get_status()
            
            if direction == Operate.DOOR_UP and upper_status == ReedSwitchStatus.CLOSED:
                self.dc_motor.stop()
                print( 'DOOR IS NOW OPEN ' )
                break
            if direction == Operate.DOOR_DOWN and lower_status == ReedSwitchStatus.CLOSED:
                self.dc_motor.stop()
                print( 'DOOR IS NOW CLOSED ' )
                self
                break
            
            if ticks > self.max_run_time:
                print('fault out')
                self.add_fault()
                break
            
            ticks += 1
            sleep(1)
        
        
    def move_door(self, direction):
        self.status = Operate.DOOR_MOTION

        if direction == Operate.DOOR_UP:
            self.dc_motor.forward(100)
        if direction == Operate.DOOR_DOWN:
            self.dc_motor.backward(100)
        
        self.operate_door(direction)
        
        self.set_door_status()
        self.operate()

    
    def _initialize_door(self):
        self.set_door_status()
        
        if self.status == Operate.DOOR_MOTION:
            self.move_door(Operate.DOOR_DOWN)
            
    def init(self):
        self._initialize_door()
        self._initialize_times()
        self.operate()
        
 
    def handle_button_override(self, direction):

        if direction == Operate.DOOR_UP and self.status == Operate.DOOR_CLOSED:
            self.status = Operate.DOOR_MOTION
            self.dc_motor.forward(100)
            self.operate_door(direction)
        if direction == Operate.DOOR_DOWN and self.status == Operate.DOOR_OPEN:
            self.status = Operate.DOOR_MOTION
            self.dc_motor.forward(100)            
            self.operate_door(direction)

        while True:
             if self.reset_button.value():
                break
        self.operate()
    
            
    def operate(self):
               
        while self.status != Operate.DOOR_MOTION or self.fault <= 1:
            now = self.rtc.get_time()
            day = self._get_day(now)
            current_hour = self._get_hour(now)
            
            self.set_door_status()
            
            if up_button.value():
                print(" button up", self.status)
                self.handle_button_override(Operate.DOOR_UP)
                break
            
            if down_button.value():
                print("buttton down ", self.status)
                self.handle_button_override(Operate.DOOR_DOWN)
                break
            
            if (day != self.day):
                print("c") 
                self.day = day
                break
                            
            sun_times = self._get_up_down_hours(now)
            
            print(f"Up: {sun_times["up"]}, down: {sun_times["down"]}, hour: {current_hour}") 
            print(f" status = {self.status}, fault: {self.fault}")
            
            if current_hour < sun_times["up"]  and self.status == Operate.DOOR_OPEN:
                self.move_door(Operate.DOOR_DOWN)
                break
            
            if sun_times["up"] < current_hour and current_hour < sun_times["down"] and self.status == Operate.DOOR_CLOSED:
                print("d")
                self.move_door(Operate.DOOR_UP)
                break
            if sun_times["down"] < current_hour and self.status == Operate.DOOR_OPEN:
                print("e")
                self.move_door(Operate.DOOR_DOWN)
                print("final")
                break
            
            sleep(1)



up_button = Pin(15, Pin.IN, Pin.PULL_DOWN)
down_button = Pin(14, Pin.IN, Pin.PULL_DOWN)
reset_button = Pin(13, Pin.IN, Pin.PULL_DOWN)

lat = 42.2293
lon = -72.7301
coords = {'longitude' : lon, 'latitude' : lat}
sun = Sun(coords, -4)

rtc_i2c = I2C(0, scl=Pin(17), sda=Pin(16))  # Using GP17 for SCL and GP16 for SDA)
rtc = DS3231(rtc_i2c)

frequency = 1000
pin1 = Pin(3, Pin.OUT)
pin2 = Pin(4, Pin.OUT)
enable = PWM(Pin(2), frequency)
dc_motor = DCMotor(pin1, pin2, enable, 15000, 65535)


upper_reed_switch_pin = 'GP18'
lower_reed_switch_pin = 'GP19'

op = Operate(dc_motor, up_button, down_button, reset_button, rtc, upper_reed_switch_pin, lower_reed_switch_pin, sun, 40)




