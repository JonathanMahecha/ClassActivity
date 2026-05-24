from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "clinic.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-in-production"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: object) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    if session.get("patient_id"):
        return redirect(url_for("list_doctors"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not full_name or not email or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("register.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO patients(full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (
                    full_name,
                    email,
                    generate_password_hash(password),
                    datetime.now().isoformat(),
                ),
            )
            db.commit()
            flash("Paciente registrado con éxito. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Ese correo ya está registrado.", "danger")

    return render_template("register.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not full_name or not email or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("register.html")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO patients(full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (
                    full_name,
                    email,
                    generate_password_hash(password),
                    datetime.now().isoformat(),
                ),
            )
            db.commit()
            flash("Paciente registrado con éxito. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Ese correo ya está registrado.", "danger")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("index"))

@app.route("/doctors")
@login_required
def list_doctors():
    db = get_db()
    doctors = db.execute(
        "SELECT id, full_name, specialty FROM doctors ORDER BY full_name"
    ).fetchall()
    return render_template("doctors.html", doctors=doctors)


@app.route("/doctors/<int:doctor_id>/slots")
@login_required
def available_slots(doctor_id: int):
    db = get_db()
    doctor = db.execute(
        "SELECT id, full_name, specialty FROM doctors WHERE id = ?", (doctor_id,)
    ).fetchone()

    slots = db.execute(
        """
        SELECT
            s.id,
            s.start_time,
            CASE WHEN a.id IS NULL THEN 1 ELSE 0 END AS is_available
        FROM slots s
        LEFT JOIN appointments a ON a.slot_id = s.id AND a.status = 'scheduled'
        WHERE s.doctor_id = ?
        ORDER BY s.start_time
        """,
        (doctor_id,),
    ).fetchall()

    return render_template("slots.html", doctor=doctor, slots=slots)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
