import logging

class SQLQueryFilter(logging.Filter):
    def filter(self, record):
        # Get the log message (the SQL query)
        message = record.getMessage()

        # Define the table name you want to exclude
        excluded_table = 'django_celery_beat_periodictask'

        # Check if the query involves the excluded table (consider different quoting styles)
        if excluded_table in message or f'"{excluded_table}"' in message or f"'{excluded_table}'" in message:
            return False  # Exclude queries involving this table

        # Otherwise, allow the query if it involves modifying queries (INSERT, UPDATE, DELETE)
        if any(sql_keyword in message for sql_keyword in ('INSERT INTO', 'UPDATE', 'DELETE FROM')):
            return True

        return False  # Exclude other queries
