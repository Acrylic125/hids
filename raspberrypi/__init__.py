import time
import requests
import RPi.GPIO as GPIO
import spidev
import I2C_LCD_driver
import threading
from KeypadListener import run_device_keypad
import subprocess
import uuid

# import RPIMock as GPIO
# import spidevMock as spidev

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Keypad
KEYPAD_MATRIX = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']
]  # layout of keys on keypad
ROW = [6, 20, 19, 13]  # row pins
COL = [12, 5, 16]  # column pins

# PINS
PIR_PIN = 17
LED_PIN = 24
BUZZER_PIN = 18

# SPI Channels
LDR_CHANNEL = 0

# SPI setup
spi = spidev.SpiDev()
spi.open(0, 0)

# PIR Sensor setup
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# set column pins as outputs, and write default value of 1 to each
for i in range(3):
    GPIO.setup(COL[i], GPIO.OUT)
    GPIO.output(COL[i], 1)

# set row pins as inputs, with pull up
for j in range(4):
    GPIO.setup(ROW[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)

driver_lcd = I2C_LCD_driver.lcd()

print("Starting up Raspberry Pi")
time.sleep(5)
print("Ready to go!")

ACTIVATION_ALWAYS = "ALWAYS"
ACTIVATION_LIGHTS_OFF = "LIGHTS_OFF"
ACTIVATION_DISABLED = "DISABLED"


def readadc(adcnum):
    if adcnum > 7 or adcnum < 0:
        return -1
    spi.max_speed_hz = 1350000
    r = spi.xfer2([1, 8 + adcnum << 4, 0])
    data = ((r[1] & 3) << 8) + r[2]
    return data


def run(*popenargs, **kwargs):
    input = kwargs.pop("input", None)
    check = kwargs.pop("handle", False)

    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = subprocess.PIPE

    process = subprocess.Popen(*popenargs, **kwargs)
    try:
        stdout, stderr = process.communicate(input)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if check and retcode:
        raise subprocess.CalledProcessError(
            retcode, process.args, output=stdout, stderr=stderr)
    return retcode, stdout, stderr


class MotionDetector:
    def __init__(self, pin):
        self.activated = False
        self.pin = pin

    def is_active(self):
        return self.activated

    def run(self):
        if GPIO.input(self.pin) == 0:
            if not self.activated:
                self.activated = True
        else:
            if self.activated:
                self.activated = False


class SPIComponent:
    def __init__(self, channel):
        self.value = 0
        self.channel = channel

    def get_value(self):
        return self.value

    def run(self):
        self.value = readadc(self.channel)


class KeypadComponent:
    def __init__(self, col_pins, row_pins, keypad_values):
        self.col_pins = col_pins
        self.row_pins = row_pins
        self.keypad_values = keypad_values

    def get_value_from_keypad(self):
        values = []
        for i in range(3):
            GPIO.output(self.col_pins[i], 0)
            for j in range(4):
                if GPIO.input(self.row_pins[j]) == 0:
                    values.append(self.keypad_values[j][i])
                    while GPIO.input(self.row_pins[j]) == 0:
                        pass
            GPIO.output(self.col_pins[i], 1)
        return values


class LCDComponent:
    def __init__(self, lcd):
        self.lcd = lcd
        self.brightness = 0

    def clear(self):
        self.lcd.lcd_clear()
        self.lcd.backlight(0)

    def set_text(self, texts):
        self.lcd.lcd_clear()
        print("Brightness: " + str(self.brightness))
        self.lcd.backlight(self.brightness)
        for i in range(len(texts)):
            self.lcd.lcd_display_string(texts[i], i + 1)


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


class CameraComponent:

    def capture(self):
        file_path = "captures/" + str(uuid.uuid4()) + ".jpg"
        print("Running Camera, saving as file name " + file_path)
        run(["fswebcam", file_path])
        return file_path


class DeviceClient:
    def __init__(self, device_id):
        self.device_id = device_id

    def send_data(self, data):
        # requests.post(self.base_url, json=data)
        pass


class Device:
    def __init__(self, id, name, activation_mode, trigger_duration, cooldown, motion_detector, led, buzzer, ldr, keypad,
                 lcd, camera):
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
        self.ldr = ldr
        self.keypad = keypad
        self.lcd = lcd
        self.camera = camera
        self.client = None

    def is_active(self):
        return self._active

    def is_within_trigger_time(self):
        return (self.last_triggered + self.trigger_duration) > time.time()

    def should_trigger(self):
        # print('Should trigger is_motion_detected: ' + str(self.is_motion_detected()) + ' is_light_detected: ' + str(self.is_light_detected()) + ' is_within_trigger_time: ' + str(self.is_within_trigger_time()) + ' activation_mode: ' + self.activation_mode)
        return self.is_motion_detected() \
               and (self.last_triggered + self.cooldown) < time.time() and \
               (self.activation_mode == ACTIVATION_ALWAYS or (
                       self.activation_mode == ACTIVATION_LIGHTS_OFF and self.is_light_detected()))

    def is_motion_detected(self):
        return self.motion_detector.is_active()

    def is_light_detected(self):
        return self.ldr.get_value() < 200

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
        self.camera.run()

    def trigger(self):
        self.toggle_lights(True)
        self.toggle_sirens(True)

        capture_image = self.camera.capture()

        capture_file = {'file': open(capture_image, 'rb')}
        response = requests.post(base_url + "devices/1/captures", files=capture_file)
        print(response.json())

        self.last_triggered = time.time()
        self._active = True

    def end_trigger(self):
        self.toggle_lights(False)
        self.toggle_sirens(False)
        self._active = False

    def run(self):
        if self.client is not None:
            self.motion_detector.run()
            self.led.run()
            self.buzzer.run()
            self.ldr.run()


device = {
    "id": "1",
    'name': 'Raspberry Pi',
    'triggerDuration': 1,
    'activationMode': ACTIVATION_ALWAYS,
    'cooldown': 5
}

motion_detector = MotionDetector(PIR_PIN)
led_component = OutputComponent(LED_PIN)
buzzer_component = OutputComponent(BUZZER_PIN)
ldr_component = SPIComponent(LDR_CHANNEL)
keypad_component = KeypadComponent(COL, ROW, KEYPAD_MATRIX)
lcd_component = LCDComponent(driver_lcd)
camera_component = CameraComponent()

device = Device(
    id=device['id'],
    name=device['name'],
    activation_mode=device['activationMode'],
    trigger_duration=device['triggerDuration'],
    cooldown=device['cooldown'],
    motion_detector=motion_detector,
    led=led_component,
    buzzer=buzzer_component,
    ldr=ldr_component,
    keypad=keypad_component,
    lcd=lcd_component,
    camera=camera_component
)

base_url = "http://127.0.0.1:5000/"


def on_connect(device_name, device_password):
    data = {
        'name': device_name,
        'password': device_password
    }
    response = requests.post(base_url + 'devices/auth', json=data)
    device.client = None
    payload = response.json()
    isOk = payload.get('ok')
    if not isOk:
        lcd_component.brightness = 0
        print('Error: ' + payload.get('message'))
        return
    data = payload.get('data')
    if data is not None and data.get("id") is not None:
        lcd_component.brightness = 1
        device.client = DeviceClient(data.get('id'))
        print('Connected Device with device id, ' + str(data.get('id')))
        return
    lcd_component.brightness = 0
    print('Failed to Connected Device')


def on_new_device(device_name, device_password):
    data = {
        'name': device_name,
        'password': device_password
    }
    response = requests.post(base_url + 'devices', json=data)
    device.client = None
    payload = response.json()
    isOk = payload.get('ok')
    if not isOk:
        lcd_component.brightness = 0
        print('Error: ' + payload.get('message'))
        return
    data = payload.get('data')
    if data is not None:
        lcd_component.brightness = 1
        device.client = DeviceClient(data.get('id'))
        print('Created Device with device id, ' + str(data.get('id')))
        return
    lcd_component.brightness = 0
    print('Failed to Create Device')


def run_main():
    call = 0
    while True:
        device.run()
        # lcd_component.set_text([str(device.is_motion_detected()), str(device.is_light_detected())])
        # print('keypad_component: {}'.format(keypad_component.get_value_from_keypad()))
        if device.is_active() and not device.is_within_trigger_time():
            print("Stopped Triggering" + str(call))
            device.end_trigger()
        if device.should_trigger():
            call = call + 1
            print('Triggering' + str(call))
            device.trigger()
        time.sleep(0.1)


device_keypad = threading.Thread(
    target=lambda: run_device_keypad(lcd=lcd_component, keypad=keypad_component, on_connect=on_connect,
                                     on_new_device=on_new_device)
)
main_thread = threading.Thread(target=lambda: run_main())

# Start threads
device_keypad.start()
main_thread.start()

# Join threads
device_keypad.join()
main_thread.join()