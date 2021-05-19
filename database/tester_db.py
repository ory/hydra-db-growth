import time


def save_result_to_sqlite(db,
                          action,
                          data={'cycle': 0, 'registered_clients': 0, 'service': 'hydra', 'size_unit': 'MB', 'results': []}):
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO Services (SERVICE_NAME) VALUES (?)", (data['service'],))
        db.commit()
    except:
        pass

    cursor.execute("SELECT SERVICE_ID FROM Services WHERE SERVICE_NAME = ?", (data['service'],))
    service_id = cursor.fetchone()[0]

    for x in data['results']:
        try:
            cursor.execute("INSERT INTO Tables (TABLE_NAME, SERVICE_ID) "
                           "VALUES(?, ?)",
                           (f'{data["service"]}_{x[0]}', service_id))
            db.commit()
        except:
            pass

        cursor.execute("SELECT TABLE_ID FROM Tables WHERE TABLE_NAME = ? AND SERVICE_ID = ?",
                       (f'{data["service"]}_{x[0]}', service_id,))
        table_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO DBGrowth (TIME, CYCLE, REGISTERED_CLIENTS, ACTION, SIZE, SIZE_UNIT, SERVICE_ID, TABLE_ID) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (int(time.time()), data['cycle'], data['registered_clients'], action,
             (int(x[1]) / 1024 / 1024), data['size_unit'],
             service_id, table_id,))

        db.commit()
