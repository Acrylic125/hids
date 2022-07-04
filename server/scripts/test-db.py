import repository
# result = repository.findDeviceSettings(1)
device = repository.create_device(name="1", password="123")
# result = repository.findDeviceCaptures(1)
# settings = repository.findAllSettings()
# print(settings)

# result = repository.update_device_settings(1, {"lightsDuration": 420, "tailwind": True, "sirensDuration": 20, "activationMode": "ALWAYS"})
# result = repository.find_device_settings(1)

print(device)

