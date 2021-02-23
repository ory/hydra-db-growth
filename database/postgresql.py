import psycopg2


class PostgresqlController:

    def __init__(self, connection=None):
        if connection:
            self.connection = connection
        else:
            self.connection = {'host': "127.0.0.1", 'port': "5432",
                               'name': "hydra", 'username': "hydra", 'password': "secret"}

        self.conn = self._pg_connection()

    def _pg_connection(self):
        return psycopg2.connect(user=self.connection['username'],
                                password=self.connection['password'],
                                host=self.connection['host'],
                                port=self.connection['port'],
                                dbname=self.connection['name'])

    def table_size_query(self):
        cursor = self.conn.cursor()
        # pg_total_relation_size(relid) will get the total size + index of the table
        # pg_total_size(relid) will only get the total size of the table
        cursor.execute(
            "SELECT relname as table_name, pg_size_pretty(pg_total_relation_size(relid)) as data_size " +
            "FROM pg_catalog.pg_statio_user_tables " +
            "ORDER BY pg_relation_size(relid) desc")

        return cursor.fetchall()
