class DatabaseException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class DatabaseController:

    def __init__(self, database):
        """
        a wrapper for database connectors
        :param database: database connection
        """
        self.database = database

    def gen_hydra_report(self):
        return self.database.table_size_query()

    def get_registered_clients(self):
        return self.database.get_registered_clients()[0]

    def get_dsn(self):
        return self.database.dsn