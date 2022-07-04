class Setting:

    def __init__(self, default_value):
        self.default_value = default_value

    def deserialize(self, value):
        pass

    def serialize(self, value):
        pass


class SettingImpl(Setting):
    def __init__(self, default_value, serializer, deserializer):
        super().__init__(default_value)
        self.serializer = serializer
        self.deserializer = deserializer

    def deserialize(self, value):
        return self.deserializer(value)

    def serialize(self, value):
        return self.serializer(value)


def create_setting(default_value, serializer, deserializer):
    return SettingImpl(default_value, serializer, deserializer)


def val_validate_float(value):
    if type(value) is float or type(value) is int:
        return value
    raise ValueError("Value must be float or int")


def val_validate_activation_mode(value):
    if value in ["ALWAYS", "LIGHTS_OFF", "DISABLED"]:
        return value
    raise ValueError("Value must be one of: ALWAYS, LIGHTS_OFF, DISABLED")


def deserialize_float(serialized, default_value):
    try:
        return float(serialized)
    except ValueError:
        return default_value


def deserialize_activation_mode(serialized, default_value):
    if serialized in ["ALWAYS", "LIGHTS_OFF", "DISABLED"]:
        return serialized
    return default_value


settings = {
    "lightsDuration": create_setting(
        30,
        lambda x: str(val_validate_float(x)),
        lambda x: deserialize_float(x, 30)),
    "sirensDuration": create_setting(
        30,
        lambda x: str(val_validate_float(x)),
        lambda x: deserialize_float(x, 30)),
    "activationMode": create_setting(
        "ALWAYS",
        lambda x: str(val_validate_activation_mode(x)),
        lambda x: deserialize_activation_mode(x, "ALWAYS")),
}
