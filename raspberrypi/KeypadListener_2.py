import time


class TextInput:
    def __init__(self, context, header, on_enter):
        self.context = context
        self.header = header
        self.on_enter = on_enter
        self.collector = []

    def on_init(self):
        pass

    def on_close(self):
        pass

    def run(self):
        print(self.header + " (* del, # enter):", ''.join(self.collector))
        chars = self.context.get_char()
        for char in chars:
            if char == '*':
                self.collector.pop()
            elif char == '#':
                if self.on_enter is not None:
                    self.on_enter(''.join(self.collector))
            else:
                self.collector.append(char)


class DeviceCredentialsMode:
    def __init__(self, context, on_complete):
        self.context = context
        self.on_complete = on_complete
        self.device_name = None
        self.device_password = None
        self.current_input = TextInput(self.context, "Device name:", lambda device_name: self.on_device_name_entered(device_name))

    def on_device_password_entered(self, device_password):
        self.device_password = device_password
        self.on_complete(self.device_name, self.device_password)

    def on_device_name_entered(self, device_name):
        self.device_name = device_name
        self.current_input = TextInput(self.context, "Device password:", self.on_device_password_entered)

    def on_init(self):
        pass

    def on_close(self):
        pass

    def run(self):
        self.current_input.run()


class OptionsRenamerMode:
    def __init__(self, context):
        self.context = context

    def on_init(self):
        print("Choose a Device option", "1. New, 2. Connect")

    def on_close(self):
        pass

    def new_device(self, device_name, device_password):
        print("New device", device_name, device_password)
        self.context.reset()

    def connect_device(self, device_name, device_password):
        print("Connect device", device_name, device_password)

    def run(self):
        option = self.context.get_char()
        if option == ['1']:
            self.context.set_mode(DeviceCredentialsMode(self.context, lambda device_name, device_password: self.new_device(device_name, device_password)))
        elif option == ['2']:
            self.context.set_mode(DeviceCredentialsMode(self.context, lambda device_name, device_password: self.connect_device(device_name, device_password)))


class KeypadListener:

    def __init__(self):
        self.mode = OptionsRenamerMode(self)
        self.mode.on_init()

    def reset(self):
        self.set_mode(OptionsRenamerMode(self))

    def run(self):
        self.mode.run()

    def set_mode(self, mode):
        if self.mode is not None:
            self.mode.on_close()
        self.mode = mode
        self.mode.on_init()

    def get_char(self):
        return [input("Enter a character: ")]


def run_device_keypad():
    renamer = KeypadListener()
    while True:
        renamer.run()
        time.sleep(0.1)


if __name__ == "__main__":
    run_device_keypad()
