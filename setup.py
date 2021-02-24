import mysql.connector
from database import cursor

DB_NAME = 'mainDB'

def create_database():
    cursor.execute(
        "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format
        (DB_NAME))
    print("database {} created!".format(DB_NAME))

create_database()