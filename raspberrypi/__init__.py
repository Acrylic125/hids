import time
import requests
import RPi.GPIO as GPIO
import spidev
import I2C_LCD_driver
import threading
# from KeypadListener import run_device_keypad
from Keypad import HomeState, HIDSKeypad, TextIO
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

    def pull_settings(self):
        response = requests.get(base_url + 'devices/' + str(self.device_id) + '/settings')
        return response


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

        # Capture Image
        capture_image = self.camera.capture()

        capture_file = {'file': open(capture_image, 'rb')}
        response = requests.post(base_url + "devices/" + self.id + "/captures", files=capture_file)
        print(response.json())

        self.last_triggered = time.time()
        # Notify Users

        try:
            response = requests.post(base_url + "notify-users", json={'deviceid': self.id})
            print(str(response.json()))
        except Exception as e:
            print(str(e))

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


default_device = {
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
    id=default_device['id'],
    name=default_device['name'],
    activation_mode=default_device['activationMode'],
    trigger_duration=default_device['triggerDuration'],
    cooldown=default_device['cooldown'],
    motion_detector=motion_detector,
    led=led_component,
    buzzer=buzzer_component,
    ldr=ldr_component,
    keypad=keypad_component,
    lcd=lcd_component,
    camera=camera_component
)
hids_keypad = HIDSKeypad(
    io=TextIO(keypad=keypad_component, lcd=lcd_component),
    initial_keypad_state=None,
    new_device=(lambda name, password: on_new_device(name, password)),
    connect=(lambda name, password: on_connect(name, password)),
)
hids_keypad.set_state(HomeState(hids_keypad))

base_url = "https://kisekixcel01.pythonanywhere.com/" # "http://127.0.0.1:5000/"


def on_connect(device_name, device_password):
    try:
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
            lcd_component.set_text(['Connection Failed'])
            time.sleep(3)
            return
        data = payload.get('data')
        if data is not None and data.get("id") is not None:
            device.id = str(data.get('id'))
            device.client = DeviceClient(data.get('id'))
            pull_settings()
            print('Connected Device with device id, ' + str(data.get('id')))
            lcd_component.set_text(['Connected!'])
            time.sleep(3)
            return
        print('Failed to Create Device')
        lcd_component.set_text(['Connection Failed'])
        time.sleep(3)
    except Exception as e:
        print('Error: ' + str(e))
        lcd_component.set_text(['Connection Failed'])
        time.sleep(3)


def on_new_device(device_name, device_password):
    try:
        data = {
            'name': device_name,
            'password': device_password
        }
        response = requests.post(base_url + 'devices', json=data)
        device.client = None
        payload = response.json()
        isOk = payload.get('ok')
        if not isOk:
            print('Error: ' + payload.get('message'))
            lcd_component.set_text(['Creation Failed'])
            time.sleep(3)
            return
        data = payload.get('data')
        if data is not None:
            device.id = str(data.get('id'))
            device.client = DeviceClient(data.get('id'))
            pull_settings()
            print('Created Device with device id, ' + str(data.get('id')))
            lcd_component.set_text(['Created!'])
            time.sleep(3)
            return
        print('Failed to Create Device')
        lcd_component.set_text(['Creation Failed'])
        time.sleep(3)
    except Exception as e:
        print('Error: ' + str(e))
        lcd_component.set_text(['Creation Failed'])
        time.sleep(3)


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


def pull_settings():
    try:
        response = device.client.pull_settings()
        if response is not None:
            payload = response.json()
            isOk = payload.get('ok')
            if not isOk:
                print('Error: ' + payload.get('message'))
                pass
            data = payload.get('data')
            if data is not None:
                device.activation_mode = data.get('activationMode')
                if device.activation_mode is None:
                    device.activation_mode = ACTIVATION_ALWAYS
                device.trigger_duration = data.get('triggerDuration')
                if device.trigger_duration is None:
                    device.trigger_duration = 5
                device.cooldown = data.get('cooldown')
                if device.cooldown is None:
                    device.cooldown = 10
    except Exception as e:
        print('Error: ' + str(e))


def run_pull():
    while True:
        if device.client is not None:
            pull_settings()
        time.sleep(5)


def run_keypad():
    while True:
        hids_keypad.run()
        time.sleep(0.1)


device_keypad = threading.Thread(target=lambda: run_keypad())
main_thread = threading.Thread(target=lambda: run_main())
update_device_thread = threading.Thread(target=lambda: run_pull())

# Start threads
device_keypad.start()
main_thread.start()
update_device_thread.start()

# Join threads
device_keypad.join()
main_thread.join()
update_device_thread.join()
