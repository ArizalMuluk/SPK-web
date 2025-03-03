import os

import bcrypt
import MySQLdb
import numpy as np
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

        cursor = mysql.connection.cursor()

        # Cek di tabel admin terlebih dahulu
        cursor.execute(
            "SELECT id_admin, username, password, role FROM tbl_admin WHERE username = %s",
            (username,),
        )
        user = cursor.fetchone()

        if user:
            # Verifikasi password admin
            stored_password = user[2]
            if bcrypt.checkpw(
                password.encode("utf-8"), stored_password.encode("utf-8")
            ):
                session["logged_in"] = True
                session["username"] = username
                session["role"] = "admin"
                session["user_id"] = user[0]

                flash("Login berhasil sebagai admin!", "success")
                return redirect(url_for("dashboard"))
        else:
            # Jika bukan admin, cek di tabel mahasiswa
            cursor.execute(
                "SELECT id_mahasiswa, nim, password FROM tbl_mahasiswa WHERE nim = %s",
                (username,),
            )
            user = cursor.fetchone()

            if user:
                stored_password = user[2]
                if bcrypt.checkpw(
                    password.encode("utf-8"), stored_password.encode("utf-8")
                ):
                    session["logged_in"] = True
                    session["username"] = username
                    session["role"] = "mahasiswa"
                    session["user_id"] = user[0]

                    flash("Login berhasil sebagai mahasiswa!", "success")
                    return redirect(url_for("mahasiswa_dashboard"))
                else:
                    flash("Password salah.", "error")
            else:
                flash("Username tidak ditemukan.", "error")

        cursor.close()

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
    # Periksa apakah user sudah login dan adalah admin
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for("mahasiswa_dashboard"))

    return render_template("dashboard.html", username=session.get("username"))


@app.route("/mahasiswa")
def mahasiswa_dashboard():
    if not session.get("logged_in") or session.get("role") != "mahasiswa":
        flash("Silakan login sebagai mahasiswa.", "error")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Hitung total penilaian
    cursor.execute(
        """
        SELECT COUNT(*) FROM tbl_penilaian 
        WHERE id_mahasiswa = (
            SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s
        )
    """,
        (session["username"],),
    )
    total_penilaian = cursor.fetchone()[0]

    # Hitung total aspirasi
    cursor.execute(
        """
        SELECT COUNT(*) FROM tbl_aspirasi
        WHERE id_mahasiswa = (
            SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s
        )
    """,
        (session["username"],),
    )
    total_aspirasi = cursor.fetchone()[0]

    cursor.close()

    return render_template(
        "mahasiswa_dashboard.html",
        username=session.get("username"),
        total_penilaian=total_penilaian,
        total_aspirasi=total_aspirasi,
    )


# Route untuk menu sidebar (placeholders)
@app.route("/data")
def view_data():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch Aspirasi Data
    cursor.execute("""
        SELECT a.id_aspirasi, m.nim, a.deskripsi, a.tanggal 
        FROM tbl_aspirasi a 
        JOIN tbl_mahasiswa m ON a.id_mahasiswa = m.id_mahasiswa
    """)
    aspirasi_data = cursor.fetchall()

    # Fetch Dosen Data
    cursor.execute("SELECT * FROM tbl_dosen")
    dosen_data = cursor.fetchall()

    # Fetch Kriteria Data
    cursor.execute("SELECT * FROM tbl_kriteria")
    kriteria_data = cursor.fetchall()

    # Fetch Penilaian Data with related information (hapus kolom tanggal)
    cursor.execute("""
        SELECT p.id_penilaian, m.nim, d.nama as nama_dosen, 
               k.nama_kriteria, p.nilai
        FROM tbl_penilaian p
        JOIN tbl_mahasiswa m ON p.id_mahasiswa = m.id_mahasiswa
        JOIN tbl_dosen d ON p.id_dosen = d.id_dosen
        JOIN tbl_kriteria k ON p.id_kriteria = k.id_kriteria
    """)
    penilaian_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "dt_view.html",
        username=session.get("username"),
        aspirasi_data=aspirasi_data,
        dosen_data=dosen_data,
        kriteria_data=kriteria_data,
        penilaian_data=penilaian_data
    )


@app.route("/add/aspirasi", methods=["POST"])
def add_aspirasi():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    try:
        deskripsi = request.form["deskripsi"]
        cursor = mysql.connection.cursor()

        # Dapatkan id_mahasiswa dari session username (NIM)
        cursor.execute(
            "SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s",
            (session["username"],),
        )
        id_mahasiswa = cursor.fetchone()[0]

        # Insert aspirasi
        cursor.execute(
            "INSERT INTO tbl_aspirasi (id_mahasiswa, deskripsi, tanggal) VALUES (%s, %s, NOW())",
            (id_mahasiswa, deskripsi),
        )

        mysql.connection.commit()
        cursor.close()

        flash("Aspirasi berhasil ditambahkan!", "success")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "error")

    return redirect(url_for("add_data"))


@app.route("/add/dosen", methods=["POST"])
def add_dosen():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    try:
        nama_dosen = request.form["nama_dosen"]
        nid = request.form["nid"]
        matkul = request.form["matkul"]

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO tbl_dosen (nama, nid, matkul) VALUES (%s, %s, %s)", 
            (nama_dosen, nid, matkul)
        )

        mysql.connection.commit()
        cursor.close()

        flash("Data dosen berhasil ditambahkan!", "success")
    except MySQLdb.IntegrityError as e:
        if "Duplicate entry" in str(e) and "nid" in str(e):
            flash(f"NID {nid} sudah terdaftar.", "error")
        else:
            flash(f"Terjadi kesalahan database: {str(e)}", "error")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "error")

    return redirect(url_for("add_data"))


def calculate_weights(comparison_matrix):
    """
    Menghitung bobot menggunakan metode AHP
    """
    # Normalisasi matriks
    matrix_sum = np.sum(comparison_matrix, axis=0)
    normalized_matrix = comparison_matrix / matrix_sum

    # Hitung bobot (rata-rata baris)
    weights = np.mean(normalized_matrix, axis=1)

    # Hitung Consistency Ratio
    n = len(comparison_matrix)
    eigenvalue = np.sum(matrix_sum * weights)
    ci = (eigenvalue - n) / (n - 1)  # Consistency Index
    ri = {
        1: 0,
        2: 0,
        3: 0.58,
        4: 0.9,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
    }  # Random Index
    cr = ci / ri[n]  # Consistency Ratio

    if cr < 0.1:  # CR harus < 0.1 untuk konsistensi yang baik
        return weights * 100  # Konversi ke persentase
    else:
        raise ValueError("Matriks perbandingan tidak konsisten (CR > 0.1)")


@app.route("/add/kriteria", methods=["POST"])
def add_kriteria():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    try:
        kriteria_names = request.form.getlist("kriteria_name[]")
        bobots = request.form.getlist("bobot[]")

        # Validasi total bobot = 100
        total_bobot = sum(int(bobot) for bobot in bobots)
        if total_bobot != 100:
            flash("Total bobot harus 100%", "error")
            return redirect(url_for("add_data"))

        cursor = mysql.connection.cursor()
        
        # Simpan setiap kriteria
        for name, bobot in zip(kriteria_names, bobots):
            cursor.execute(
                "INSERT INTO tbl_kriteria (nama_kriteria, bobot) VALUES (%s, %s)",
                (name, float(bobot)/100)  # Konversi persen ke desimal
            )

        mysql.connection.commit()
        cursor.close()

        flash("Kriteria berhasil ditambahkan!", "success")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "error")

    return redirect(url_for("add_data"))


@app.route("/add/penilaian", methods=["POST"])
def add_penilaian():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    try:
        id_dosen = request.form["dosen"]
        id_kriteria = request.form["kriteria"]
        nilai = request.form["nilai"]

        cursor = mysql.connection.cursor()

        # Dapatkan id_mahasiswa dari session username (NIM)
        cursor.execute(
            "SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s",
            (session["username"],),
        )
        id_mahasiswa = cursor.fetchone()[0]

        # Insert penilaian
        cursor.execute(
            """INSERT INTO tbl_penilaian 
               (id_mahasiswa, id_dosen, id_kriteria, nilai, tanggal) 
               VALUES (%s, %s, %s, %s, NOW())""",
            (id_mahasiswa, id_dosen, id_kriteria, nilai),
        )

        mysql.connection.commit()
        cursor.close()

        flash("Penilaian berhasil ditambahkan!", "success")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "error")

    return redirect(url_for("add_data"))


# Modifikasi route add_data untuk menyediakan data dropdown
@app.route("/add")
def add_data():
    if not session.get("logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Hanya admin yang dapat mengakses halaman ini.", "error")
        return redirect(url_for("mahasiswa_dashboard"))

    cursor = mysql.connection.cursor()

    # Fetch dosen untuk dropdown
    cursor.execute("SELECT id_dosen, nama FROM tbl_dosen")
    dosen_list = cursor.fetchall()

    # Fetch kriteria untuk dropdown
    cursor.execute("SELECT id_kriteria, nama_kriteria FROM tbl_kriteria")
    kriteria_list = cursor.fetchall()

    cursor.close()

    return render_template(
        "add_dt.html",
        username=session.get("username"),
        dosen_list=dosen_list,
        kriteria_list=kriteria_list,
    )


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


@app.route("/mahasiswa/penilaian")
def mahasiswa_penilaian():
    if not session.get("logged_in") or session.get("role") != "mahasiswa":
        flash("Silakan login sebagai mahasiswa.", "error")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Ambil daftar dosen
    cursor.execute("SELECT id_dosen, nama FROM tbl_dosen")
    dosen_list = cursor.fetchall()

    # Ambil daftar kriteria
    cursor.execute("SELECT id_kriteria, nama_kriteria FROM tbl_kriteria")
    kriteria_list = cursor.fetchall()

    # Ambil penilaian yang sudah diberikan
    cursor.execute(
        """
        SELECT d.nama, k.nama_kriteria, p.nilai 
        FROM tbl_penilaian p
        JOIN tbl_dosen d ON p.id_dosen = d.id_dosen
        JOIN tbl_kriteria k ON p.id_kriteria = k.id_kriteria
        WHERE p.id_mahasiswa = (
            SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s
        )
    """,
        (session["username"],),
    )
    penilaian_existing = cursor.fetchall()

    cursor.close()

    return render_template(
        "mahasiswa_penilaian.html",
        username=session.get("username"),
        dosen_list=dosen_list,
        kriteria_list=kriteria_list,
        penilaian_existing=penilaian_existing,
    )


@app.route("/mahasiswa/aspirasi")
def mahasiswa_aspirasi():
    if not session.get("logged_in") or session.get("role") != "mahasiswa":
        flash("Silakan login sebagai mahasiswa.", "error")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Ambil aspirasi yang sudah diberikan
    cursor.execute(
        """
        SELECT deskripsi, tanggal 
        FROM tbl_aspirasi 
        WHERE id_mahasiswa = (
            SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s
        )
        ORDER BY tanggal DESC
    """,
        (session["username"],),
    )
    aspirasi_list = cursor.fetchall()

    cursor.close()

    return render_template(
        "mahasiswa_aspirasi.html",
        username=session.get("username"),
        aspirasi_list=aspirasi_list,
    )


@app.route("/mahasiswa/hasil")
def mahasiswa_hasil():
    if not session.get("logged_in") or session.get("role") != "mahasiswa":
        flash("Silakan login sebagai mahasiswa.", "error")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Ambil hasil perhitungan SAW
    cursor.execute(
        """
        SELECT d.nama, 
               ROUND(SUM(p.nilai * k.bobot) / SUM(k.bobot), 2) as nilai_akhir
        FROM tbl_penilaian p
        JOIN tbl_dosen d ON p.id_dosen = d.id_dosen
        JOIN tbl_kriteria k ON p.id_kriteria = k.id_kriteria
        GROUP BY d.id_dosen, d.nama
        ORDER BY nilai_akhir DESC
    """
    )
    hasil_penilaian = cursor.fetchall()

    cursor.close()

    return render_template(
        "mahasiswa_hasil.html",
        username=session.get("username"),
        hasil_penilaian=hasil_penilaian,
    )


@app.route("/mahasiswa/penilaian/add", methods=["POST"])
def add_mahasiswa_penilaian():
    if not session.get("logged_in") or session.get("role") != "mahasiswa":
        flash("Silakan login sebagai mahasiswa.", "error")
        return redirect(url_for("login"))

    try:
        id_dosen = request.form["dosen"]
        cursor = mysql.connection.cursor()

        # Dapatkan id_mahasiswa
        cursor.execute(
            "SELECT id_mahasiswa FROM tbl_mahasiswa WHERE nim = %s",
            (session["username"],),
        )
        id_mahasiswa = cursor.fetchone()[0]

        # Ambil semua kriteria
        cursor.execute("SELECT id_kriteria FROM tbl_kriteria")
        kriteria_list = cursor.fetchall()

        # Insert penilaian untuk setiap kriteria
        for kriteria in kriteria_list:
            nilai = request.form.get(f"nilai_{kriteria[0]}")
            if nilai:
                cursor.execute(
                    """INSERT INTO tbl_penilaian 
                       (id_mahasiswa, id_dosen, id_kriteria, nilai, tanggal) 
                       VALUES (%s, %s, %s, %s, NOW())""",
                    (id_mahasiswa, id_dosen, kriteria[0], nilai),
                )

        mysql.connection.commit()
        cursor.close()

        flash("Penilaian berhasil ditambahkan!", "success")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "error")

    return redirect(url_for("mahasiswa_penilaian"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
