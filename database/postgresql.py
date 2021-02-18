import psycopg2


class PostgresqlController:

    def __init__(self, connection=None):
        if connection:
            self.connection = connection
        else:
            self.connection = {'host': "127.0.0.1", 'port': "5432",
                               'database': "hydra", 'user': "hydra", 'password': "secret"}

        self.conn = self._pg_connection()

    def _pg_connection(self):
        return psycopg2.connect(user=self.connection.user,
                                password=self.connection.password,
                                host=self.connection.host,
                                port=self.connection.port,
                                dbname=self.connection.database)

    def table_size_query(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT relname as table_name, pg_size_pretty(pg_relation_size(%s) as data_size " +
            "FROM pg_catalog.pg_statio_user_tables " +
            "ORDER BY pg_relation_size(relid) desc;"
            , self.connection.database)
