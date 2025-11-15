from time import sleep
from reed import ReedSwitchStatus, ReedSwitchControl
from machine import Pin
import sys

led = Pin("LED", Pin.OUT)

def log(msg):
    entry = f"[LOG] {msg}"
    print(entry)

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
        self.sun = sun

        self.up_time = params['UP_RUN_TIME']
        self.max_run_time = params['MAX_RUN_TIME']
        self.reed_buffer = params['REED_BUFFER']

        self.status = None
        self.fault = 0
        self.dc_motor.stop()
        self._initialize_door()


    def _initialize_door(self):
        led.toggle()
        self.fault_indicator(0)
        self.manual_indicator(0)
        self._set_door_status()
        log(f"Initialized status: {self.status}")

    def engage_door(self):
        if self.status is not DoorStatus.CLOSED:
            self._automated_door_move(DoorDirection.DOWN)   
        self._operate()
            
    def _add_fault(self):
        log("Adding Fault")
        led.toggle()
        self.fault += 1
        self.fault_indicator(1)
        self.motion_indicator(0)
        self.dc_motor.stop()


    def _set_door_status(self):
        upper = ReedSwitchControl(self.upper_reed).get_status()
        lower = ReedSwitchControl(self.lower_reed).get_status()

        statuses = {
            (ReedSwitchStatus.OPEN, ReedSwitchStatus.OPEN): DoorStatus.MOTION,
            (ReedSwitchStatus.CLOSED, ReedSwitchStatus.OPEN): DoorStatus.OPEN,
            (ReedSwitchStatus.OPEN, ReedSwitchStatus.CLOSED): DoorStatus.CLOSED,
        }

        status_key = (upper, lower)
        new_status = statuses.get(status_key, None)
        old_status = self.status

        log(f"_set_door_status: upper={upper}, lower={lower}, old={old_status}, new={new_status}")

        if new_status is None:
            self._add_fault()
            return

        # only skip update if still in motion and reeds are still open
        if new_status == DoorStatus.MOTION and old_status == DoorStatus.MOTION:
            return

        self.status = new_status


    def _get_up_down_hours(self, time_tuple):
        sun_times = self.sun.getSunTimes(time_tuple)
        return {
            "up": sun_times["sunrise"]["decimal"] - 1,
            "down": sun_times["sunset"]["decimal"] + 0.5,
        }

    def _get_hour(self, time):
        hour, mins = time[3:5]
        return round(hour + mins / 60, 4)
    
    def _operate_door(self, direction):
        # Move motor, track ticks, and buffer after reed

        ticks = 0
        check_adjustment = 3.5
        
        log(f"Operating door {direction}...")
        if direction == DoorDirection.UP:
            self.dc_motor.forward(100)
        elif direction == DoorDirection.DOWN:
            self.dc_motor.backward(100)
        self.status = DoorStatus.MOTION
        self.motion_indicator(1)
        sleep(2) # clear reeds 
            
            
        while self.status == DoorStatus.MOTION:
            lower_status = ReedSwitchControl(self.lower_reed).get_status()
            upper_status = ReedSwitchControl(self.upper_reed).get_status()

            log(f"tick={ticks}, direction={direction}, upper={upper_status}, lower={lower_status}")

            if direction == DoorDirection.UP and upper_status == ReedSwitchStatus.CLOSED:
                sleep(.8)
                self.motion_indicator(0)
                self.dc_motor.stop()
                self.status = DoorStatus.OPEN
                break

            if direction == DoorDirection.DOWN and lower_status == ReedSwitchStatus.CLOSED:
                sleep(.8)
                self.motion_indicator(0)
                self.dc_motor.stop()
                self.status = DoorStatus.CLOSED
                break

            # safety timeout
            if ticks > self.max_run_time * check_adjustment:
                self._add_fault()
                break

            ticks += 1
            sleep(0.2)


        sleep(self.reed_buffer) ## buffer before returning to operation
        self._set_door_status()

    def _automated_door_move(self, direction):
        log(f"Automated move: {direction}")

        self._operate_door(direction)
        self._set_door_status()
        
    def _manual_action(self, direction):
        log(f"Manual Action: {direction}", )
        if self.status == DoorStatus.MOTION:
            return
        if direction == DoorDirection.UP and self.status == DoorStatus.CLOSED:
            self._operate_door(direction)
        if direction == DoorDirection.DOWN and self.status == DoorStatus.OPEN:
            self._operate_door(direction)

    def _override_door(self, direction):
        log(f"Manual override: {direction}", )
        
        self.manual_indicator(1)
        try:
            self._manual_action(direction)

            while True:
                if self.reset_button.value():
                    self.manual_indicator(0)
                    break
                if self.up_button.value():
                    self._manual_action(DoorDirection.UP)
                    sleep(1)
                if self.down_button.value():
                    self._manual_action(DoorDirection.DOWN)
                    sleep(1)
                sleep(1)
        except Exception as e:
            log(f"Override error: {e}")
            self.dc_motor.stop()


    def _update_position_indicator(self, blink_state):
        """
        Independent door monitor
        """
        upper_status = ReedSwitchControl(self.upper_reed).get_status()
        lower_status = ReedSwitchControl(self.lower_reed).get_status()

        if upper_status == ReedSwitchStatus.CLOSED:
            self.manual_indicator(blink_state)
        else:
            self.manual_indicator(0)
        
        if lower_status == ReedSwitchStatus.CLOSED:
            self.motion_indicator(blink_state)
        else:
            self.motion_indicator(0)
        

    def _operate(self):
        log(f"Entering operate loop | faults={self.fault}, status={self.status}")
        blink_state = 0
        try:
            if self.fault >= 1:
                raise Exception("faults present")

            while self.fault < 1:
                now = self.rtc.get_time()
                current_hour = self._get_hour(now)
                self._set_door_status()
                sun_times = self._get_up_down_hours(now)
                  
                if self.up_button.value():
                    self._override_door(DoorDirection.UP)
                if self.down_button.value():
                    self._override_door(DoorDirection.DOWN)
                
                #Indicate of the door is open
                blink_state = 1 - blink_state
                self._update_position_indicator(blink_state)
                
                ## signal door open status
                if self.status == DoorStatus.OPEN:
                    self.fault_indicator(1)
                    self.manual_indicator(1)  
                elif self.status == DoorStatus.CLOSED:
                    self.fault_indicator(0)
                    self.manual_indicator(0)

                # sun based operations
                if current_hour < sun_times["up"] and self.status == DoorStatus.OPEN:
                    self._automated_door_move(DoorDirection.DOWN)
                elif sun_times["up"] < current_hour < sun_times["down"] and self.status == DoorStatus.CLOSED:
                    self._automated_door_move(DoorDirection.UP)
                elif current_hour > sun_times["down"] and self.status == DoorStatus.OPEN:
                    self._automated_door_move(DoorDirection.DOWN)

                sleep(1)

        except Exception as e:
            log(f"Erroring out: {e}")
            self.fault_indicator(1)
            led.toggle()
            self._update_position_indicator(True)#Red + Blue = Error open Red+White Error Closed 
            self.dc_motor.stop()
            sys.exit()

