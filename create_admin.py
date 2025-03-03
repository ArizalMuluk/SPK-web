import os

import bcrypt
import MySQLdb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi database
db = MySQLdb.connect(
    host=os.environ.get("MYSQL_HOST"),
    user=os.environ.get("MYSQL_USER"),
    passwd=os.environ.get("MYSQL_PASSWORD"),
    db=os.environ.get("MYSQL_DB"),
)


def create_admin_table():
    cursor = db.cursor()

    # Buat tabel admin jika belum ada
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tbl_admin (
            id_admin INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'admin'
        )
    """
    )

    db.commit()
    cursor.close()


def create_admin(username, password):
    cursor = db.cursor()

    try:
        # Hash password
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Insert admin
        cursor.execute(
            "INSERT INTO tbl_admin (username, password) VALUES (%s, %s)",
            (username, hashed),
        )

        db.commit()
        print(f"Admin dengan username '{username}' berhasil dibuat!")

    except MySQLdb.IntegrityError:
        print(f"Username '{username}' sudah digunakan!")
    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")
    finally:
        cursor.close()


def main():
    create_admin_table()

    print("=== Buat Akun Admin ===")
    username = input("Masukkan username admin: ")
    password = input("Masukkan password admin: ")

    create_admin(username, password)

    db.close()


if __name__ == "__main__":
    main()
