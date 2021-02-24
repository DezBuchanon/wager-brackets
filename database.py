import mysql.connector

config = {
    'user': 'root',
    'password': '99Inches!',
    'host': 'localhost'
}

db = mysql.connector.connect(**config)
cursor = db.cursor()