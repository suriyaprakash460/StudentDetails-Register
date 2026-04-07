import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="suriya@2004",
    database="student_db"
)

print("Connected da bro ")