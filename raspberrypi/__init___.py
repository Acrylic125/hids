import time
import requests
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# PINS
PIR_PIN = 17
LED_PIN = 24
BUZZER_PIN = 18

# PIR Sensor setup
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

print("Starting up Raspberry Pi")
time.sleep(5)
print("Ready to go!")

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

class MotionDetector:
    def __init__(self, pin):
        self.activated = False
        self.pin = pin

    def is_active(self):
        return self.activated

    def run(self):
        if GPIO.input(self.pin):
            if not self.activated:
                self.activated = True
        else:
            if self.activated:
                self.activated = False


class OutputComponent:
    def __init__(self, pin):
        self.activated = False
        self.pin = pin

    def set_activated(self, activated):
        self.activated = activated

    def is_active(self):
        return self.activated

    def run(self):
        if self.activated:
            GPIO.output(self.pin, 1)
        else:
            GPIO.output(self.pin, 0)


class Device:
    def __init__(self, id, name, activation_mode, trigger_duration, cooldown, motion_detector, led, buzzer):
        self.id = id
        self.name = name
        self.activation_mode = activation_mode
        self.trigger_duration = trigger_duration
        self.cooldown = cooldown
        self.last_triggered = 0
        self._active = False
        self.motion_detector = motion_detector
        self.led = led
        self.buzzer = buzzer

    def is_active(self):
        return self._active

    def is_within_trigger_time(self):
        return (self.last_triggered + self.trigger_duration) > time.time()

    def should_trigger(self):
        return self.is_motion_detected() and (self.last_triggered + self.cooldown) < time.time() and\
               (self.activation_mode == ACTIVATION_ALWAYS or
                (self.activation_mode == ACTIVATION_LIGHTS_OFF and self.is_light_detected()))

    def is_motion_detected(self):
        return self.motion_detector.is_active()

    def is_light_detected(self):
        return False

    def is_lights_on(self):
        return self.led.is_active()

    def is_sirens_on(self):
        return self.buzzer.is_active()

    def toggle_lights(self, toggle):
        print('Lights {}', toggle)
        self.led.set_activated(toggle)

    def toggle_sirens(self, toggle):
        print('Sirens {}', toggle)
        self.buzzer.set_activated(toggle)

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

    def run(self):
        self.motion_detector.run()
        self.led.run()
        self.buzzer.run()


device = {
    "id": "1",
    'name': 'Raspberry Pi',
    'triggerDuration': 5,
    'activationMode': ACTIVATION_ALWAYS,
    'cooldown': 15
}

motion_detector = MotionDetector(PIR_PIN)
led_component = OutputComponent(LED_PIN)
buzzer_component = OutputComponent(BUZZER_PIN)

device = Device(
    id=device['id'],
    name=device['name'],
    activation_mode=device['activationMode'],
    trigger_duration=device['triggerDuration'],
    cooldown=device['cooldown'],
    motion_detector=motion_detector,
    led=led_component,
    buzzer=buzzer_component
)


while True:
    if device.is_active() and not device.is_within_trigger_time():
        print("Stopped Triggering")
        device.end_trigger()
    if device.should_trigger():
        print('Triggering')
        device.trigger()
    device.run()
    time.sleep(0.1)
