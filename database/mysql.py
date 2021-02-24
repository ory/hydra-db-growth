import mysql.connector


class MysqlController:

    def __init__(self, connection=None):
        if connection:
            self.connection = connection
        else:
            self.connection = {'host': "127.0.0.1", 'port': "3306", 'name': "hydra",
                               'username': "root", 'password': "secret"}

        self.conn = self._mysql_connection()

    def _mysql_connection(self):
        return mysql.connector.connect(user=self.connection['username'],
                                       password=self.connection['password'],
                                       host=self.connection['host'],
                                       port=self.connection['port'],
                                       database=self.connection['name'])

    def table_size_query(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT TABLE_NAME AS `Table`, ROUND((DATA_LENGTH + INDEX_LENGTH)) AS `Size (Bytes)` " +
            "FROM information_schema.TABLES " +
            "WHERE TABLE_SCHEMA = %s " +
            "ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC"
            , (self.connection['name'],)
            )
        return cursor.fetchall()

    def get_registered_clients(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM hydra_client"
            )
        return cursor.fetchone()