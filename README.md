# Decision Support System (DSS) (English) / Sistem Pendukung Keputusan (SPK) (Indonesia)

A web-based Decision Support System application using Flask and MySQL.

## Description

This application is a decision support system that allows users to manage aspiration data, lecturers, criteria, and assessments. The application is built with Flask and uses MySQL as the database.

## Features

- User authentication (login and register)
- Interactive dashboard
- Data management (aspirations, lecturers, criteria, assessments)
- Data calculation and analysis
- Light and dark themes

## System Requirements

- Python 3.10+
- MySQL Server
- Modern web browser

## Installation Guide

### 1. Clone Repository
```bash
git clone https://github.com/ArizalMuluk/SPK-web.git
cd SPK-web
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Database Configuration
- Create a new MySQL database
- Copy the `.env.example` file to `.env`
- Edit the `.env` file and adjust it to your database configuration:
```bash
SECRET_KEY=your-secret-key
MYSQL_HOST=localhost
MYSQL_USER=your-mysql-username
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=your-database-name
```

### 4. Create Database Structure
```bash
CREATE TABLE tbl_mahasiswa (
    id_mahasiswa INT AUTO_INCREMENT PRIMARY KEY,
    nim VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE tbl_dosen (
    id_dosen INT AUTO_INCREMENT PRIMARY KEY,
    nid VARCHAR(20) UNIQUE NOT NULL,
    nama VARCHAR(100) NOT NULL,
    matkul VARCHAR(100) NOT NULL
);

CREATE TABLE tbl_kriteria (
    id_kriteria INT AUTO_INCREMENT PRIMARY KEY,
    nama_kriteria VARCHAR(100) NOT NULL,
    bobot FLOAT NOT NULL
);

CREATE TABLE tbl_aspirasi (
    id_aspirasi INT AUTO_INCREMENT PRIMARY KEY,
    id_mahasiswa INT NOT NULL,
    deskripsi TEXT NOT NULL,
    tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mahasiswa) REFERENCES tbl_mahasiswa(id_mahasiswa)
);

CREATE TABLE tbl_penilaian (
    id_penilaian INT AUTO_INCREMENT PRIMARY KEY,
    id_mahasiswa INT NOT NULL,
    id_dosen INT NOT NULL,
    id_kriteria INT NOT NULL,
    nilai FLOAT NOT NULL,
    FOREIGN KEY (id_mahasiswa) REFERENCES tbl_mahasiswa(id_mahasiswa),
    FOREIGN KEY (id_dosen) REFERENCES tbl_dosen(id_dosen),
    FOREIGN KEY (id_kriteria) REFERENCES tbl_kriteria(id_kriteria)
);

CREATE TABLE tbl_admin (
    id_admin INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin'
);
```

### 5. Run the Application
```bash
python app.py
```

The application will run at [http://localhost:8080](http://localhost:8080) (or the port specified in the `.env` file).

## Usage

- Open the application in a browser
- Register a new account or login if you already have an account
- Use the sidebar menu for navigation:
  - Dashboard: View general information
  - View Data: View and manage data
  - Add Data: Add new data
  - Calculation: Perform DSS calculations
  - Analysis Results: View analysis results
  - Settings: Change application theme

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
4. Push to your fork and create a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.
