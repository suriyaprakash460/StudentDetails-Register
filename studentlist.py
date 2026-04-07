import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="suriya@2004",
    database="student_db"
)

cursor = conn.cursor()

name = input("Enter name: ").strip()
age = int(input("Enter age: "))
course = input("Enter course: ").strip()

query = "INSERT INTO students (name, age, course) VALUES (%s, %s, %s)"
values = (name, age, course)

cursor.execute(query, values)
conn.commit()

print("Student added!")

# View students
cursor.execute("SELECT * FROM students")
result = cursor.fetchall()

print("\nStudent List:")

for row in result:
    print("ID:", row[0], "| Name:", row[1], "| Age:", row[2], "| Course:", row[3])
