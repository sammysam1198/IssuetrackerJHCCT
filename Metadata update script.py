
cur.execute(
    '''
INSERT INTO store_devices
        (device_uid, store_number, device_type, device_number, manufacturer, model, device_notes)
        VALUES %s
        ON CONFLICT (device_uid) DO UPDATE SET
            store_number = EXCLUDED.store_number,
            device_type = EXCLUDED.device_type,
            device_number = EXCLUDED.device_number,
            manufacturer = EXCLUDED.manufacturer,
            model = EXCLUDED.model,
            device_notes = EXCLUDED.device_notes,
            updated_at = NOW();
    '''
)