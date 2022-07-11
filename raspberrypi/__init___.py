import time
import requests


ACTIVATION_ALWAYS = "ALWAYS"
ACTIVATION_LIGHTS_OFF = "LIGHTS_OFF"
ACTIVATION_DISABLED = "DISABLED"


# Adapted from
# https://stackoverflow.com/questions/10154568/postpone-code-for-later-execution-in-python-like-settimeout-in-javascript
# class FutureAction:
#     def __init__(self, action, time):
#         self.action = action
#         self.time = time
#
#     def execute(self):
#         if time.time() > self.time:
#             self.action()
#             return True
#         return False
#
#
# class Futures:
#     def __init__(self):
#         self.futures = []
#
#     def add(self, future):
#         self.futures.append(future)
#
#     def execute(self):
#         for future in self.futures:
#             if future.execute():
#                 self.futures.remove(future)
#
#     def clear(self):
#         self.futures = []
#

class Device:
    def __init__(self, id, name, activation_mode, trigger_duration, cooldown):
        self.id = id
        self.name = name
        self.activation_mode = activation_mode
        self.trigger_duration = trigger_duration
        self.cooldown = cooldown
        self.last_triggered = 0
        self._active = False

    def is_active(self):
        return self._active

    def is_within_trigger_time(self):
        return (self.last_triggered + self.trigger_duration) > time.time()

    def should_trigger(self):
        return self.is_motion_detected() and (self.last_triggered + self.cooldown) < time.time() and\
               (self.activation_mode == ACTIVATION_ALWAYS or
                (self.activation_mode == ACTIVATION_LIGHTS_OFF and self.is_light_detected()))

    def is_motion_detected(self):
        return True

    def is_light_detected(self):
        return False

    def is_lights_on(self):
        return False

    def is_sirens_on(self):
        return False

    def toggle_lights(self, toggle):
        print('Lights {}', toggle)

    def toggle_sirens(self, toggle):
        print('Sirens {}', toggle)

    def capture_image(self):
        print('Capture image')

    def trigger(self):
        self.last_triggered = time.time()
        self.toggle_lights(True)
        self.toggle_sirens(True)
        self.capture_image()
        self._active = True

    def end_trigger(self):
        self.toggle_lights(False)
        self.toggle_sirens(False)
        self._active = False


device = {
    "id": "1",
    'name': 'Raspberry Pi',
    'triggerDuration': 15,
    'activationMode': ACTIVATION_ALWAYS,
    'cooldown': 15
}


device = Device(
    id=device['id'],
    name=device['name'],
    activation_mode=device['activationMode'],
    trigger_duration=device['triggerDuration'],
    cooldown=device['cooldown']
)

while True:
    if device.is_active() and not device.is_within_trigger_time():
        device.end_trigger()
    if device.should_trigger():
        device.trigger()
    time.sleep(0.1)
