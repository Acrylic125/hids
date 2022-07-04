from db import db
from device_settings import settings as ds


def create_device(
        name=None, password=None
):
    executor = db.use_executor()
    cursor = executor.execute(
        '''INSERT INTO devices (name, password) 
           VALUES (?, ?)''', (name, password))
    executor.done()

    return {
        "id": cursor.lastrowid, "name": name, "password": password
    }


def find_device_settings(id):
    executor = db.use_executor()
    cursor = executor.execute(
        '''SELECT device_id, setting_name, value
           FROM device_settings ds 
           WHERE device_id = ?''', (id, ))
    results = cursor.fetchall()
    executor.done()

    settings = {}
    for row in results:
        setting_name, setting_value = row[1], row[2]
        setting = ds.get(setting_name)
        # print(f"Parsing {setting_name}: {setting_value}")
        if setting is None or setting_value is None:
            continue
        settings[setting_name] = setting.deserialize(setting_value)
    return settings


def find_device_captures(id):
    executor = db.use_executor()
    cursor = executor.execute(
        '''SELECT id, image_loc, capture_time
            FROM device_captures 
            WHERE device_id = ?''', (id, ))
    results = cursor.fetchall()
    executor.done()

    captures = []
    for row in results:
        captures.append({
            "id": row[0],
            "image_loc": row[1],
            "capture_time": row[2]
        })
    return captures


def find_all_devices():
    executor = db.use_executor()
    cursor = executor.execute(
        '''SELECT id, name
            FROM devices''')
    results = cursor.fetchall()
    executor.done()

    devices = []
    for row in results:
        devices.append({
            "id": row[0],
            "name": row[1],
        })
    return devices


def add_device_to_user(user_id, device_id):
    executor = db.use_executor()
    cursor = executor.execute(
        '''INSERT INTO user_devices (user_id, device_id) 
           VALUES (?, ?)''', (user_id, device_id))
    executor.done()

    return {
        "id": cursor.lastrowid
    }


def find_all_devices_for_user(userid):
    executor = db.use_executor()
    cursor = executor.execute(
        '''SELECT d.id, d.name 
            FROM devices d 
            INNER JOIN user_devices ud
                  ON d.id = ud.device_id 
            INNER JOIN users u 
                  ON ud.user_id = u.id 
            WHERE u.id = ?''', (userid, ))
    results = cursor.fetchall()
    executor.done()

    devices = []
    for row in results:
        devices.append({
            "id": row[0],
            "name": row[1],
        })
    return devices


def find_device_by_id(id):
    executor = db.use_executor()
    cursor = executor.execute(
        '''SELECT id, name 
            FROM devices 
            WHERE id = ? 
            LIMIT 1''', (id, ))
    result = cursor.fetchone()
    executor.done()

    if result is None:
        return None
    return {
        "id": result[0],
        "name": result[1]
    }


def update_device_settings(
        id, settings
):
    # Populate placeholders
    placeholders = []
    placeholder_values = []
    for setting_name, setting_value in settings.items():
        setting = ds.get(setting_name)
        if setting is None:
            continue
        serialized_value = setting.serialize(setting_value)
        placeholders.append("(?, ?, ?)")
        placeholder_values.append(id)
        placeholder_values.append(setting_name)
        placeholder_values.append(serialized_value)
    if placeholders is None:
        return False
    placeholder = ",".join(placeholders)

    # Update settings
    executor = db.use_executor()
    executor.execute(
        f'''INSERT OR REPLACE INTO device_settings (device_id, setting_name, value)
            VALUES {placeholder}''', tuple(placeholder_values))
    executor.done()
    return True
