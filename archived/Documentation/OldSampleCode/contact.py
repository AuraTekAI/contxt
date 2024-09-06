import pyodbc
import logging



from variables import *
from db_ops import get_database_connection, close_database_resources
from push_email_gui import process_emails

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


