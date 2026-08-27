import mysql.connector
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="careerpilot"
)
cursor = db.cursor()
print("Database Connected Successfully")