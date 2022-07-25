CREATE TABLE IF NOT EXISTS devices (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            password TEXT,
            UNIQUE(name)
    );

CREATE TABLE IF NOT EXISTS device_captures (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            device_id INT NOT NULL,
            image_loc TEXT NOT NULL,
            capture_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
    );

CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            email TEXT,
            password TEXT,
            UNIQUE(username),
            UNIQUE(email)
    );

CREATE TABLE IF NOT EXISTS device_settings (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            device_id INT NOT NULL,
            setting_name VARCHAR(255) NOT NULL,
            value TEXT,
            UNIQUE(device_id, setting_name),
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    );

CREATE TABLE IF NOT EXISTS user_devices (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INT NOT NULL,
            device_id INT NOT NULL,
            UNIQUE(user_id, device_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    );

CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            user_id INT NOT NULL,
            chat_id INT NOT NULL,
            UNIQUE(user_id, chat_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

-- INSERT INTO users(username, email, password)
--        VALUES ('u111','u111@gmail.com','p111');

-- INSERT INTO devices(name, password)
--        VALUES ('d2', 'd2');

-- INSERT INTO device_captures(device_id, image_loc, capture_time)
--     VALUES (1, 'abc.png', '1-1-2022 00:00:00'),
--             (1, 'def.png', '1-5-2022 00:00:00'),
--             (1, 'ghi.png', '1-10-2022 00:00:00'),
--             (1, 'jkl.png', '4-15-2022 00:00:00');
