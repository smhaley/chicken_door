# chicken_door
Manage your coop door


# Hardware
 - Controller: py pico with MicroPython
 - Motor Controller: L298N
 - Motor: 12v Worm Geared Motor with desired RPM
 - Real Time Clock: ds3231
 - Reed Switches (two)

# Setup
## Location 
Configure the following settings in [`main.py`](./src/main.py) 

- `lat`: local latitude
- `lon`: local longitude   
- `time_offset`: timezone offset from GMT time (do not use local daylight savings times)

The Following are determined by local door design
- `MAX_RUN_TIME`: maximum number of seconds the system may run before shutting down due to an error
- `UP_RUN_TIME`: time the system may move in the upware position,
- `REED_BUFFER`: time in seconds the motor continues to run after reed contact -- ensure contact

## Wiring
Diagram to come.

Wire all switches per PIN numbers foun in main.py -- or update per needs. 

## Internal clock
Run [`set_time.py`](./src/utils/set_time.py) with the machine time set to the desire localtime in _standard time_ (remove the hour if initial setup is during _savings time_).







![chicken knight](./assets/imgs/chicken_knight.jpeg "chicken knight")