import os

import mysql.connector


def setup_database():
    try:
        database = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME"),
        )

        cursor = database.cursor(buffered=True)

        cursor.execute("SHOW DATABASES")

        for name in cursor:
            if os.getenv("DATABASE_NAME") in name:
                return database, cursor
    except mysql.connector.errors.ProgrammingError:
        database = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
        )
        cursor = database.cursor(buffered=True)
        cursor.execute(f"CREATE DATABASE {os.getenv('DATABASE_NAME')}")

    database = mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        database=os.getenv("DATABASE_NAME"),
    )
    cursor = database.cursor(buffered=True)

    # User table
    cursor.execute(
        "CREATE TABLE user ("
        "discord_id INT UNIQUE NOT NULL PRIMARY KEY,"
        "username VARCHAR(255) NOT NULL"
        ");"
    )
    # Month table
    cursor.execute(
        "CREATE TABLE month ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "month VARCHAR(255) NOT NULL,"
        "year INT NOT NULL"
        ");"
    )
    # Meme table
    cursor.execute(
        "CREATE TABLE meme ("
        "id INT AUTO_INCREMENT PRIMARY KEY, "
        "name VARCHAR(255) NOT NULL,"
        "attachment VARCHAR(255),"
        "month int NOT NULL,"
        "FOREIGN KEY (month) REFERENCES month(id)"
        ");"
    )
    # Vote table
    cursor.execute(
        "CREATE TABLE vote ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "user INT NOT NULL,"
        "meme INT NOT NULL,"
        "FOREIGN KEY (user) REFERENCES user(discord_id),"
        "FOREIGN KEY (meme) REFERENCES meme(id)"
        ");"
    )

    return database, cursor
