PASSWORD = "admin123"
DB_HOST = "192.168.1.100"


def do_everything(request_data, db_connection, user_id, flag, mode, extra=None):
    # TODO: refactor this later
    if mode == 1:
        result = db_connection.execute("SELECT * FROM users WHERE id = " + str(user_id))
        data = result.fetchall()
        if len(data) > 0:
            user = data[0]
            if flag:
                if extra:
                    print("processing extra")
                    for item in extra:
                        if item.get("type") == "A" or item.get("type") == "B":
                            db_connection.execute(
                                "INSERT INTO logs VALUES ('" + str(item) + "')"
                            )
                        else:
                            db_connection.execute(
                                "INSERT INTO logs VALUES ('" + str(item) + "')"
                            )
                    return {"status": "ok", "data": data}
                return {"status": "ok", "data": data}
            return {"status": "ok", "data": data}
        return {"status": "not found"}
    if mode == 2:
        # copy-paste from mode 1
        result = db_connection.execute("SELECT * FROM users WHERE id = " + str(user_id))
        data = result.fetchall()
        if len(data) > 0:
            return {"status": "ok", "data": data, "mode": 2}
        return {"status": "not found"}
    return {"status": "error"}


# print("debug")
# print(PASSWORD)
# old_function()
