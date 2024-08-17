from time import sleep
from reed import ReedSwitchStatus, ReedSwitchControl

class DoorDirection:
    UP = 'up'
    DOWN = 'down'

class DoorStatus:
    OPEN = 'open'
    CLOSED = 'closed'
    MOTION = 'motion'

class Operate:
   
    def __init__(self, dc_motor, up_button, down_button, reset_button, rtc, upper_reed_switch_pin, lower_reed_switch_pin, sun, max_run_time = 40):       
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
        self.max_run_time = max_run_time
        
        self.dc_motor.stop()
        
    def _add_fault(self):
        self.fault += 1
        self.dc_motor.stop()
    
    def _set_door_status(self):
        status_key = (self.upper_reed.get_status(), self.lower_reed.get_status())
        
        statuses = {
        (ReedSwitchStatus.OPEN, ReedSwitchStatus.OPEN): DoorStatus.MOTION,
        (ReedSwitchStatus.CLOSED, ReedSwitchStatus.OPEN): DoorStatus.OPEN,
        (ReedSwitchStatus.OPEN, ReedSwitchStatus.CLOSED): DoorStatus.CLOSED
        }
        
        if status_key in statuses:
            self.status = statuses[status_key]
        else:
            self._add_fault()            
        
    def _get_up_down_hours(self, time_tuple):
        sun_times = self.sun.getSunTimes(time_tuple)
        sun_rise = sun_times["sunrise"]["decimal"]
        sun_set = sun_times["sunset"]["decimal"]
        return {"up": sun_rise, "down": sun_set}
    
    def _get_hour(self, time):
        hour, mins = time[3:5]
        return round( hour + mins/60, 4)
    
    def _operate_door(self, direction):
        ticks = 0
        while self.status == DoorStatus.MOTION:
                        
            upper_status = self.upper_reed.get_status()
            lower_status = self.lower_reed.get_status()
            
            if direction == DoorDirection.UP and upper_status == ReedSwitchStatus.CLOSED:
                self.dc_motor.stop()
                print( 'DOOR IS NOW OPEN ' )
                break
            if direction == DoorDirection.DOWN and lower_status == ReedSwitchStatus.CLOSED:
                self.dc_motor.stop()
                print( 'DOOR IS NOW CLOSED ' )
                self
                break
            
            print(ticks)
            
            if ticks > self.max_run_time:
                self._add_fault()
                break
            
            ticks += 1
            sleep(1)
        self._set_door_status()    
        
        
        
    def _automated_door_move(self, direction):
        self.status = DoorStatus.MOTION
        print('handle move door',  direction == DoorDirection.DOWN, direction)
        
        if direction == DoorDirection.UP:
            self.dc_motor.forward(100)
        if direction == DoorDirection.DOWN:
            self.dc_motor.backward(100)
        
        self._operate_door(direction)
        self._set_door_status()
        self._operate()
        
        
    def engage_door(self):
        self._operate()
        
    def _override_door(self, direction):
        try:
            print('override', direction, self.status, direction == DoorDirection.UP and self.status == DoorStatus.CLOSED)
            
            if direction == DoorDirection.UP and self.status == DoorStatus.CLOSED:
                self.status = DoorStatus.MOTION
                self.dc_motor.forward(100)
                self._operate_door(direction)
            if direction == DoorDirection.DOWN and self.status == DoorStatus.OPEN:
                self.status = DoorStatus.MOTION
                self.dc_motor.backward(100)            
                self._operate_door(direction)
            print(self.status)
            while True:
                if self.reset_button.value():
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
        try:
            while self.status != DoorStatus.MOTION and self.fault < 1:
                now = self.rtc.get_time()
                current_hour = self._get_hour(now)
                self._set_door_status()
                sun_times = self._get_up_down_hours(now)
                
                print(f" status = {self.status}, fault: {self.fault}")
                print(f"Up: {sun_times["up"]}, down: {sun_times["down"]}, hour: {current_hour}") 
                
                #button based operations
                if self.up_button.value():
                    self._override_door(DoorDirection.UP)
                    break
                
                if self.down_button.value():
                    self._override_door(DoorDirection.DOWN)
                    break
                

                #sun based operations
                if current_hour < sun_times["up"]  and self.status == DoorStatus.OPEN:
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
            self.dc_motor.stop()    
        




