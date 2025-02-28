import os

import bcrypt
import MySQLdb
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL

load_dotenv()

app = Flask(__name__, static_url_path="/static")

app.secret_key = os.environ.get("SECRET_KEY")

# Konfigurasi database menggunakan variabel lingkungan
app.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
app.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")

mysql = MySQL(app)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nim = request.form["nim"]
        password = request.form["password"]

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        try:
            curs = mysql.connection.cursor()
            curs.execute(
                "INSERT INTO tbl_mahasiswa (nim, password) VALUES (%s, %s)",
                (nim, hashed),
            )
            mysql.connection.commit()
            curs.close()

            flash("Registrasi Berhasil! Kamu bisa Login sekarang.", "success")
            return redirect(url_for("login"))

        except MySQLdb.IntegrityError as e:  # perubahan disini
            if "Duplicate entry" in str(e) and "nim" in str(e):
                flash(
                    f"NIM {nim} sudah terdaftar. Silakan gunakan NIM lain atau login jika sudah memiliki akun.",
                    "error",
                )
            else:
                flash(f"Terjadi kesalahan database: {str(e)}", "error")

            return render_template("register.html")

        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Cek user di database
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT nim, password FROM tbl_mahasiswa WHERE nim = %s", (username,)
        )
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Verifikasi password
            stored_password = user[1]
            if bcrypt.checkpw(
                password.encode("utf-8"), stored_password.encode("utf-8")
            ):
                # Jika login berhasil, buat session
                session["logged_in"] = True
                session["username"] = username

                flash("Login berhasil!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Password salah.", "error")
        else:
            flash("Username tidak ditemukan.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Hapus data session
    session.pop("logged_in", None)
    session.pop("username", None)
    flash("Anda telah berhasil logout.", "success")
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    # Periksa apakah user sudah login
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session.get("username"))


# Route untuk menu sidebar (placeholders)
@app.route("/data")
def view_data():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("data.html", username=session.get("username"))


@app.route("/add")
def add_data():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("add_data.html", username=session.get("username"))


@app.route("/calculation")
def calculation():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("calculation.html", username=session.get("username"))


@app.route("/analysis")
def analysis():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("analysis.html", username=session.get("username"))


@app.route("/settings")
def settings():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    return render_template("settings.html", username=session.get("username"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
