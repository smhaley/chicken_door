class RunParameters:
    #by voltage
    twelve = {
        'MAX_RUN_TIME': 45,
        'UP_RUN_TIME': 30,
        'REED_BUFFER': 3.0
        }
    fourteen = {
        'MAX_RUN_TIME': 45,
        'UP_RUN_TIME': 30,
        'REED_BUFFER': 3.0
        }

class LocationConfig:
    lat = 42.2293
    lon = -72.7301
    time_offset = -5
    
 
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