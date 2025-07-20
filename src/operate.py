from time import sleep
from reed import ReedSwitchStatus, ReedSwitchControl
from machine import Pin
import sys

led = Pin("LED", Pin.OUT)

class DoorDirection:
    UP = 'up'
    DOWN = 'down'

class DoorStatus:
    OPEN = 'open'
    CLOSED = 'closed'
    MOTION = 'motion'


class Operate:
   
    def __init__(self, dc_motor, buttons, indicators, rtc, reeds, sun, params):       
        self.dc_motor = dc_motor
        self.up_button = buttons.up_button
        self.down_button = buttons.down_button
        self.reset_button = buttons.reset_button
        self.fault_indicator = indicators.fault
        self.motion_indicator = indicators.motion
        self.manual_indicator = indicators.manual
        self.rtc = rtc
        self.upper_reed = reeds['upper_reed_switch']
        self.lower_reed = reeds['lower_reed_switch']
        self.up_time = params['UP_RUN_TIME']
        self.sun = sun
        self.status = None
        self.fault = 0
        self.max_run_time = params['MAX_RUN_TIME']
        self.reed_buffer = params['REED_BUFFER']
        
        self.dc_motor.stop()
        self._initialize_door()

        
    def _initialize_door(self):
        led.toggle()
        self.fault_indicator(0)
        self.manual_indicator(0)
        self._set_door_status()

        
    def _add_fault(self):
        print('LOG-> Adding Fault')
        led.toggle()
        self.fault += 1
        self.fault_indicator(1)
        self.motion_indicator(0)
        self.dc_motor.stop()
    
    def _set_door_status(self):
        lower_status = ReedSwitchControl(self.lower_reed).get_status()
        upper_status = ReedSwitchControl(self.upper_reed).get_status()
        
        status_key = (upper_status, lower_status)
        
        statuses = {
            (ReedSwitchStatus.OPEN, ReedSwitchStatus.OPEN): DoorStatus.MOTION,
            (ReedSwitchStatus.CLOSED, ReedSwitchStatus.OPEN): DoorStatus.OPEN,
            (ReedSwitchStatus.OPEN, ReedSwitchStatus.CLOSED): DoorStatus.CLOSED,
        }
        
        system_determined_status = self.status in [DoorStatus.OPEN, DoorStatus.CLOSED]
        
        if statuses[status_key] == DoorStatus.MOTION and system_determined_status:
            """Accounts for system established open/close. Adjusts for reed closure speed"""
            return 
        elif status_key in statuses:
            self.status = statuses[status_key]
        else:
            self._add_fault()            
        
    def _get_up_down_hours(self, time_tuple):
        sun_times = self.sun.getSunTimes(time_tuple)
        sun_rise = sun_times["sunrise"]["decimal"]
        sun_set = sun_times["sunset"]["decimal"]
        return {"up": sun_rise - .25, "down": sun_set + .5}
    
    def _get_hour(self, time):
        hour, mins = time[3:5]
        return round( hour + mins/60, 4)
    
    def _operate_door(self, direction):
        ticks = 0
        check_adjustment = 3.5
        self.motion_indicator(1)
        while self.status == DoorStatus.MOTION:         
            lower_status = ReedSwitchControl(self.lower_reed).get_status()
            upper_status = ReedSwitchControl(self.upper_reed).get_status()

            print('LOG-> In Motion')
            print(f'LOG-> upper reed status: {upper_status}')
            print(f'LOG-> lower reed status: {lower_status}')
            print(f'LOG-> tick counter: {ticks}' )
 
            if direction == DoorDirection.UP and (upper_status == ReedSwitchStatus.CLOSED or ticks >= self.up_time * check_adjustment):
                sleep(self.reed_buffer)
                self.motion_indicator(0)
                self.dc_motor.stop()
                self.status = DoorStatus.OPEN
                break
            if direction == DoorDirection.DOWN and lower_status == ReedSwitchStatus.CLOSED:
                sleep(self.reed_buffer)
                self.motion_indicator(0)
                self.dc_motor.stop()
                self.status = DoorStatus.CLOSED
                break
            
            if ticks > self.max_run_time * check_adjustment:
                self._add_fault()
                break
            
            ticks += 1
            sleep(.2)
        self._set_door_status()    
        
        
        
    def _automated_door_move(self, direction):
        print(f'LOG-> Automated move: {direction}')
        self.status = DoorStatus.MOTION
        if direction == DoorDirection.UP:
            self.dc_motor.forward(100)
        if direction == DoorDirection.DOWN:
            self.dc_motor.backward(100)
        
        self._operate_door(direction)
        self._set_door_status()
        self._operate()
        
        
    def engage_door(self):
        if self.status == DoorStatus.MOTION:
            self._automated_door_move(DoorDirection.DOWN)   
        self._operate()
            
        
    def _override_door(self, direction):
        print('LOG -> Overriding door')
        self.manual_indicator(1)
        try:  
            if direction == DoorDirection.UP and self.status == DoorStatus.CLOSED:
                self.status = DoorStatus.MOTION
                self.dc_motor.forward(100)
                self._operate_door(direction)
            if direction == DoorDirection.DOWN and self.status == DoorStatus.OPEN:
                self.status = DoorStatus.MOTION
                self.dc_motor.backward(100)            
                self._operate_door(direction)
            
            while True:
                if self.reset_button.value():
                    self.manual_indicator(0)
                    break
                if self.up_button.value():
                    self._override_door(DoorDirection.UP)
                    break
                
                if self.down_button.value():
                    self._override_door(DoorDirection.DOWN)
                    break
                
                sleep(1)
                
            self._operate()
        except:
            self.dc_motor.stop()
    
            
    def _operate(self):
        print('LOG -> in operate')
        print(f'LOG -> faults: {self.fault}')
        print(f'LOG -> door status: {self.status}')
        try:
            if self.fault >= 1:
                raise Exception('faults')
            while self.fault < 1:
                now = self.rtc.get_time()
                current_hour = self._get_hour(now)
                self._set_door_status()
                sun_times = self._get_up_down_hours(now)
                
                #button based operations
                if self.up_button.value():
                    self._override_door(DoorDirection.UP)
                    break
                
                if self.down_button.value():
                    self._override_door(DoorDirection.DOWN)
                    break
                

                #sun based operations
                if current_hour < sun_times["up"] and self.status == DoorStatus.OPEN:
                    self._automated_door_move(DoorDirection.DOWN)
                    break
                
                elif sun_times["up"] < current_hour and current_hour < sun_times["down"] and self.status == DoorStatus.CLOSED:
                    self._automated_door_move(DoorDirection.UP)
                    break
                elif sun_times["down"] < current_hour and self.status == DoorStatus.OPEN:
                    self._automated_door_move(DoorDirection.DOWN)
                    break
    
                sleep(1)
                
        except:
            print('LOG -> erroring out')
            self.fault_indicator(1)
            led.toggle()
            self.dc_motor.stop()
            sys.exit()

