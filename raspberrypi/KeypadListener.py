import time


class TextInput:
    def __init__(self, context, header, on_enter):
        self.context = context
        self.header = header
        self.on_enter = on_enter
        self.collector = []

    def _out(self):
        self.context.lcd.set_text([self.header + " (* del, # enter):", ''.join(self.collector)])

    def on_init(self):
        self._out()

    def on_close(self):
        pass

    def run(self):
        chars = self.context.get_char()
        for char in chars:
            if char == '*':
                if len(self.collector) > 0:
                    self.collector.pop()
                    self._out()
            elif char == '#':
                if self.on_enter is not None:
                    self.on_enter(''.join(self.collector))
            else:
                self.collector.append(char)
                self._out()


class DeviceCredentialsMode:
    def __init__(self, context, on_complete):
        self.context = context
        self.on_complete = on_complete
        self.device_name = None
        self.device_password = None
        self.current_input = TextInput(self.context, "Device name:", lambda device_name: self.on_device_name_entered(device_name))

    def _switch_input(self, text_input):
        if self.current_input is not None:
            self.current_input.on_close()
        self.current_input = text_input
        if text_input is not None:
            text_input.on_init()

    def on_device_password_entered(self, device_password):
        self.device_password = device_password
        self._switch_input(None)
        self.on_complete(self.device_name, self.device_password)

    def on_device_name_entered(self, device_name):
        self.device_name = device_name
        if self.current_input is not None:
            self.current_input.on_close()
        self._switch_input(TextInput(self.context, "Device password:", self.on_device_password_entered))

    def on_init(self):
        pass

    def on_close(self):
        pass

    def run(self):
        self.current_input.run()


class OptionsMode:
    def __init__(self, context):
        self.context = context

    def on_init(self):
        self.context.lcd.set_text(["Choose a Device option", "1. New, 2. Connect"])

    def on_close(self):
        pass

    def new_device(self, device_name, device_password):
        print("New device", device_name, device_password)
        self.context.reset()

    def connect_device(self, device_name, device_password):
        print("Connect device", device_name, device_password)
        self.context.reset()

    def run(self):
        option = self.context.get_char()
        if option == ['1']:
            print("Option 1")
            self.context.set_mode(DeviceCredentialsMode(self.context, lambda device_name, device_password: self.new_device(device_name, device_password)))
        elif option == ['2']:
            print("Option 2")
            self.context.set_mode(DeviceCredentialsMode(self.context, lambda device_name, device_password: self.connect_device(device_name, device_password)))


class KeypadListener:

    def __init__(self, lcd, keypad):
        self.lcd = lcd
        self.keypad = keypad
        self.mode = OptionsMode(self)
        self.mode.on_init()

    def reset(self):
        self.set_mode(OptionsMode(self))

    def run(self):
        self.mode.run()

    def set_mode(self, mode):
        if self.mode is not None:
            self.mode.on_close()
        self.mode = mode
        self.mode.on_init()

    def get_char(self):
        char = self.keypad.get_value_from_keypad()
        return char


def run_device_keypad(lcd, keypad):
    renamer = KeypadListener(lcd=lcd, keypad=keypad)
    while True:
        renamer.run()
        time.sleep(0.1)


