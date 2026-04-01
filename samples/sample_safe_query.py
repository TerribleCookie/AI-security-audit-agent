user = input("user: ")
query = "SELECT * FROM users WHERE name = %s"
cursor.execute(query, (user,))