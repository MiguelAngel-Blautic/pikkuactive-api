from typing import Any

import mysql.connector as mariadb


class mariaDB:
    def test(
            self: str,
    ) -> Any:
        MARIADB_DB: str = 'ziven-active'
        MARIADB_PASSWORD: str = '$Sqnon2022!'
        MARIADB_USER: str = 'root'
        MARIADB_SERVER: str = '82.223.19.236'
        MARIADB_PORT: str = '3306'

        conn = mariadb.connect(
            user=MARIADB_USER,
            password=MARIADB_PASSWORD,
            host=MARIADB_SERVER,
            port=MARIADB_PORT,
            database=MARIADB_DB
        )
        cur = conn.cursor()
        try:
            statement = self
            cur.execute(statement)
            res = cur.fetchall()
        except mariadb.Error as e:
            print(f"Error: {e}")
            res = "Error: " + e.__str__()
        conn.close()
        return res
