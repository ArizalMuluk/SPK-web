import os

import bcrypt
import MySQLdb
import numpy as np
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
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
    cursor.execute(
        """
        SELECT a.id_aspirasi, m.nim, a.deskripsi, a.tanggal 
        FROM tbl_aspirasi a 
        JOIN tbl_mahasiswa m ON a.id_mahasiswa = m.id_mahasiswa
    """
    )
    aspirasi_data = cursor.fetchall()

    # Fetch Dosen Data
    cursor.execute("SELECT * FROM tbl_dosen")
    dosen_data = cursor.fetchall()

    # Fetch Kriteria Data
    cursor.execute("SELECT * FROM tbl_kriteria")
    kriteria_data = cursor.fetchall()

    # Fetch Penilaian Data with related information (hapus kolom tanggal)
    cursor.execute(
        """
        SELECT p.id_penilaian, m.nim, d.nama as nama_dosen, 
            k.nama_kriteria, p.nilai
        FROM tbl_penilaian p
        JOIN tbl_mahasiswa m ON p.id_mahasiswa = m.id_mahasiswa
        JOIN tbl_dosen d ON p.id_dosen = d.id_dosen
        JOIN tbl_kriteria k ON p.id_kriteria = k.id_kriteria
    """
    )
    penilaian_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "dt_view.html",
        username=session.get("username"),
        aspirasi_data=aspirasi_data,
        dosen_data=dosen_data,
        kriteria_data=kriteria_data,
        penilaian_data=penilaian_data,
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
            (nama_dosen, nid, matkul),
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
    if not session.get("logged_in") or session.get("role") != "admin":
        flash("Hanya admin yang dapat mengakses fitur ini.", "error")
        return redirect(url_for("login"))

    try:
        kriteria_names = request.form.getlist("kriteria_name[]")
        bobots = request.form.getlist("bobot[]")
        jenis_list = request.form.getlist("jenis[]")
        min_values = request.form.getlist("min_nilai[]")
        max_values = request.form.getlist("max_nilai[]")

        # Validasi total bobot = 100
        total_bobot = sum(float(bobot) for bobot in bobots)
        if total_bobot != 100:
            flash("Total bobot harus 100%", "error")
            return redirect(url_for("add_data"))

        cursor = mysql.connection.cursor()

        # Simpan setiap kriteria
        for name, bobot, jenis, min_val, max_val in zip(
            kriteria_names, bobots, jenis_list, min_values, max_values
        ):
            cursor.execute(
                """INSERT INTO tbl_kriteria 
                (nama_kriteria, bobot, jenis, min_nilai, max_nilai) 
                VALUES (%s, %s, %s, %s, %s)""",
                (name, float(bobot) / 100, jenis, min_val, max_val),
            )
            kriteria_id = cursor.lastrowid

            # Simpan deskripsi untuk setiap nilai
            for nilai in range(int(min_val), int(max_val) + 1):
                deskripsi = request.form.get(f"nilai_desc_{nilai-int(min_val)}[]")
                if deskripsi:
                    cursor.execute(
                        """INSERT INTO tbl_nilai_deskripsi 
                        (id_kriteria, nilai, deskripsi) 
                        VALUES (%s, %s, %s)""",
                        (kriteria_id, nilai, deskripsi),
                    )

        mysql.connection.commit()
        cursor.close()
        flash("Kriteria berhasil ditambahkan!", "success")

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

    # Ambil daftar kriteria dengan min_nilai dan max_nilai
    cursor.execute("SELECT id_kriteria, nama_kriteria, min_nilai, max_nilai FROM tbl_kriteria")
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
        kriteria_list=kriteria_list,  # Mengirim kriteria_list yang sudah dimodifikasi
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


# Route untuk menghapus data
@app.route("/delete/<string:table>/<int:id>", methods=["POST"])
def delete_data(table, id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        cursor = mysql.connection.cursor()

        # Map table name ke nama tabel dan kolom ID yang sesuai
        table_map = {
            "aspirasi": ("tbl_aspirasi", "id_aspirasi"),
            "dosen": ("tbl_dosen", "id_dosen"),
            "kriteria": ("tbl_kriteria", "id_kriteria"),
            "penilaian": ("tbl_penilaian", "id_penilaian"),
        }

        if table not in table_map:
            return jsonify({"status": "error", "message": "Invalid table"}), 400

        table_name, id_column = table_map[table]

        # Eksekusi query delete
        cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s", (id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify(
            {"status": "success", "message": f"Data {table} berhasil dihapus"}
        )

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}),
            500,
        )


# Route untuk mengambil data untuk edit
@app.route("/get_data/<string:table>/<int:id>")
def get_data(table, id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Map table name ke query yang sesuai
        table_queries = {
            "aspirasi": "SELECT * FROM tbl_aspirasi WHERE id_aspirasi = %s",
            "dosen": "SELECT * FROM tbl_dosen WHERE id_dosen = %s",
            "kriteria": "SELECT * FROM tbl_kriteria WHERE id_kriteria = %s",
            "penilaian": """
                SELECT p.*, d.nama as nama_dosen, k.nama_kriteria 
                FROM tbl_penilaian p
                JOIN tbl_dosen d ON p.id_dosen = d.id_dosen
                JOIN tbl_kriteria k ON p.id_kriteria = k.id_kriteria
                WHERE p.id_penilaian = %s
            """,
        }

        if table not in table_queries:
            return jsonify({"status": "error", "message": "Invalid table"}), 400

        cursor.execute(table_queries[table], (id,))
        data = cursor.fetchone()
        cursor.close()

        if data:
            return jsonify({"status": "success", "data": data})
        else:
            return jsonify({"status": "error", "message": "Data not found"}), 404

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}),
            500,
        )


# Route untuk update data
@app.route("/update/<string:table>/<int:id>", methods=["POST"])
def update_data(table, id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        cursor = mysql.connection.cursor()
        data = request.form.to_dict()

        # Map table name ke query update yang sesuai
        update_queries = {
            "aspirasi": """
                UPDATE tbl_aspirasi 
                SET deskripsi = %s
                WHERE id_aspirasi = %s
            """,
            "dosen": """
                UPDATE tbl_dosen 
                SET nama = %s, nid = %s, matkul = %s
                WHERE id_dosen = %s
            """,
            "kriteria": """
                UPDATE tbl_kriteria 
                SET nama_kriteria = %s, bobot = %s
                WHERE id_kriteria = %s
            """,
            "penilaian": """
                UPDATE tbl_penilaian 
                SET nilai = %s
                WHERE id_penilaian = %s
            """,
        }

        if table not in update_queries:
            return jsonify({"status": "error", "message": "Invalid table"}), 400

        # Prepare parameters based on table
        params = {
            "aspirasi": (data["deskripsi"], id),
            "dosen": (data["nama"], data["nid"], data["matkul"], id),
            "kriteria": (data["nama_kriteria"], data["bobot"], id),
            "penilaian": (data["nilai"], id),
        }

        cursor.execute(update_queries[table], params[table])
        mysql.connection.commit()
        cursor.close()

        return jsonify(
            {"status": "success", "message": f"Data {table} berhasil diupdate"}
        )

    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Terjadi kesalahan: {str(e)}"}),
            500,
        )


@app.route("/get_deskripsi_nilai/<int:kriteria_id>")
def get_deskripsi_nilai(kriteria_id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            """SELECT nilai, deskripsi 
               FROM tbl_nilai_deskripsi 
               WHERE id_kriteria = %s 
               ORDER BY nilai""",
            (kriteria_id,),
        )
        deskripsi_list = cursor.fetchall()
        cursor.close()

        return jsonify(deskripsi_list)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Update route update_data untuk kriteria
@app.route("/update/kriteria/<int:id>", methods=["POST"])
def update_kriteria(id):
    if not session.get("logged_in") or session.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    try:
        cursor = mysql.connection.cursor()
        data = request.form

        # Update kriteria
        cursor.execute(
            """UPDATE tbl_kriteria 
               SET nama_kriteria = %s, 
                   bobot = %s,
                   jenis = %s,
                   min_nilai = %s,
                   max_nilai = %s
               WHERE id_kriteria = %s""",
            (
                data["kriteria_name"],
                float(data["bobot"]) / 100,
                data["jenis"],
                data["min_nilai"],
                data["max_nilai"],
                id,
            ),
        )

        # Update deskripsi nilai
        cursor.execute("DELETE FROM tbl_nilai_deskripsi WHERE id_kriteria = %s", (id,))

        for nilai in range(int(data["min_nilai"]), int(data["max_nilai"]) + 1):
            deskripsi = data.get(f"nilai_desc_{nilai}")
            if deskripsi:
                cursor.execute(
                    """INSERT INTO tbl_nilai_deskripsi 
                       (id_kriteria, nilai, deskripsi) 
                       VALUES (%s, %s, %s)""",
                    (id, nilai, deskripsi),
                )

        mysql.connection.commit()
        cursor.close()

        return jsonify({"status": "success", "message": "Kriteria berhasil diupdate"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
