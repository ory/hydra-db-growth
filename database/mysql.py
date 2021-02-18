import mysql.connector


class MysqlController:

    def __init__(self, connection=None):
        if connection:
            self.connection = connection
        else:
            self.connection = {'host': "127.0.0.1", 'port': "3306", 'database': "hydra",
                               'user': "root", 'password': "secret"}

        self.conn = self._mysql_connection()

    def _mysql_connection(self):
        return mysql.connector.connect(user=self.connection.user,
                                       password=self.connection.password,
                                       host=self.connection.host,
                                       port=self.connection.port,
                                       database=self.connection.database)

    def table_size_query(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT TABLE_NAME AS `Table`, ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024) AS `Size (MB)` " +
            "FROM information_schema.TABLES " +
            "WHERE TABLE_SCHEMA = '%s' " +
            "ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;"
            , self.database
            )
