from time import sleep


class TextIO:

    def __init__(self, keypad, lcd):
        self.keypad = keypad
        self.lcd = lcd

    def read(self):
        # return [input("key:")]
        char = self.keypad.get_value_from_keypad()
        print(char)
        return char

    def write(self, text):
        # for t in text:
        #     print(t)
        self.lcd.set_text(text)


class TextInput:
    def __init__(self, io, on_change, on_enter):
        self.io = io
        self.on_change = on_change
        self.on_enter = on_enter
        self.collector = []

    def collect(self):
        return ''.join(self.collector)

    def _change(self, new_char):
        if self.on_change is not None:
            self.on_change(self.collect(), new_char)

    def _enter(self):
        if self.on_enter is not None:
            self.on_enter(self.collect())

    def run(self):
        chars = self.io.read()
        for char in chars:
            if char == '*':
                if len(self.collector) > 0:
                    self.collector.pop()
                self._change(char)
            elif char == '#':
                self._enter()
            else:
                self.collector.append(char)
                self._change(char)


class HIDSKeypad:

    def __init__(self, io, initial_keypad_state, connect, new_device):
        self.io = io
        self.keypad_state = initial_keypad_state
        self.connect = connect
        self.new_device = new_device

    def set_state(self, new_state):
        if self.keypad_state is not None:
            self.keypad_state.on_close()
        self.keypad_state = new_state
        if new_state is not None:
            new_state.on_init()

    def run(self):
        print("TTTTT")
        if self.keypad_state is not None:
            self.keypad_state.run()


class CredentialsState:

    def __init__(self, context, on_complete):
        self.context = context
        self.on_complete = on_complete
        self.device_name = None
        self.device_password = None
        self.current_text_input = None

    def on_init(self):
        self.set_state_device_name()

    def on_close(self):
        pass

    def run(self):
        if self.current_text_input is not None:
            self.current_text_input.run()

    def _try_complete(self):
        is_complete = self.device_name is not None and self.device_password is not None
        if is_complete and self.on_complete is not None:
            self.on_complete(self.device_name, self.device_password)
            self.context.set_state(HomeState(self.context))
        return is_complete

    def _refresh_output_name(self, text):
        self.context.io.write(["Device name:", text])

    def _refresh_output_password(self, text):
        self.context.io.write(["Device password:", text])

    def _on_name_enter(self, text):
        if text is None or text.strip() == "":
            self.context.io.write(["Device name cannot be", "empty."])
            sleep(1)
            self._refresh_output_name(text)
        else:
            self.device_name = text
            if not self._try_complete():
                self.set_state_device_password()

    def _on_password_enter(self, text):
        if text is None or text.strip() == "":
            self.context.io.write(["Device password cannot be", "empty."])
            sleep(1)
            self._refresh_output_password(text)
            pass
        else:
            self.device_password = text
            if not self._try_complete():
                self.set_state_device_name()

    def _on_name_change(self, text, new_char):
        self._refresh_output_name(text)

    def _on_password_change(self, text, new_char):
        self._refresh_output_password(text)

    def set_state_device_name(self):
        self.current_text_input = TextInput(
            self.context.io,
            self._on_name_change,
            self._on_name_enter
        )
        self.context.io.write(["Device name:", ""])

    def set_state_device_password(self):
        self.current_text_input = TextInput(
            self.context.io,
            self._on_password_change,
            self._on_password_enter
        )
        self.context.io.write(["Device password:", ""])


# Keypad states
class HomeState:

    def __init__(self, context):
        self.context = context

    def on_init(self):
        self.context.io.write(["Choose a Device option", "1. New, 2. Connect"])

    def on_close(self):
        pass

    def run(self):
        option = self.context.io.read()
        if option == ['1']:
            self.context.set_state(CredentialsState(self.context, self.context.new_device))
        elif option == ['2']:
            self.context.set_state(CredentialsState(self.context, self.context.connect))


# hids_keypad = HIDSKeypad(
#     io=TextIO(),
#     initial_keypad_state=None,
#     new_device=(lambda name, password: print("New device:", name, password)),
#     connect=(lambda name, password: print("Connect device:", name, password))
# )
# hids_keypad.set_state(HomeState(hids_keypad))
#
# while True:
#     hids_keypad.run()
