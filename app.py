from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-production"

DATA_FILE = Path(__file__).with_name("users.json")


def load_users():
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            return []

    return data if isinstance(data, list) else []


def save_users(users):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)


def find_user(username):
    username = username.strip().lower()
    return next((user for user in load_users() if user["username"] == username), None)


def current_user():
    username = session.get("username")
    return find_user(username) if username else None


def require_user():
    user = current_user()
    if user:
        return user

    flash("Please log in first.", "error")
    return None


def workout_volume(workout):
    return (
        int(workout.get("sets", 0) or 0)
        * int(workout.get("reps", 0) or 0)
        * float(workout.get("weight", 0) or 0)
    )


def dashboard_context(user):
    workouts = sorted(
        user.get("workouts", []),
        key=lambda workout: workout.get("created_at", ""),
        reverse=True,
    )
    chart_data = [
        {
            "label": f"{workout.get('exercise', 'Workout')} {workout.get('created_at', '')[:10]}".strip(),
            "volume": workout_volume(workout),
        }
        for workout in reversed(workouts)
    ]

    return {
        "user": user,
        "workouts": workouts,
        "total_workouts": len(workouts),
        "total_volume": sum(item["volume"] for item in chart_data),
        "max_weight": max((float(workout.get("weight", 0) or 0) for workout in workouts), default=0),
        "chart_data": chart_data,
    }


@app.route("/")
def home():
    if session.get("username"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login.html")
def login_html():
    return redirect(url_for("login"))


@app.route("/signup.html")
def signup_html():
    return redirect(url_for("signup"))


@app.route("/dashboard.html")
def dashboard_html():
    return redirect(url_for("dashboard"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not username or not password:
            flash("Please fill in every signup field.", "error")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("signup"))

        users = load_users()
        if any(user["username"] == username for user in users):
            flash("That username is already taken.", "error")
            return redirect(url_for("signup"))

        users.append(
            {
                "name": name,
                "username": username,
                "password": generate_password_hash(password),
                "workouts": [],
            }
        )
        save_users(users)
        session["username"] = username
        flash("Account created. Welcome to your dashboard.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user(username)

        if not user or not check_password_hash(user["password"], password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        session["username"] = user["username"]
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    user = require_user()
    if not user:
        return redirect(url_for("login"))

    return render_template("dashboard.html", **dashboard_context(user))


@app.route("/workouts", methods=["POST"])
def add_workout():
    user = require_user()
    if not user:
        return redirect(url_for("login"))

    exercise = request.form.get("exercise", "").strip()
    sets = request.form.get("sets", "").strip()
    reps = request.form.get("reps", "").strip()
    weight = request.form.get("weight", "").strip()

    if not exercise or not sets or not reps or not weight:
        flash("Exercise, sets, reps, and weight are required.", "error")
        return redirect(url_for("dashboard"))

    try:
        sets_count = int(sets)
        reps_count = int(reps)
        weight_amount = float(weight)
    except ValueError:
        flash("Sets, reps, and weight must be valid numbers.", "error")
        return redirect(url_for("dashboard"))

    if sets_count <= 0 or reps_count <= 0 or weight_amount < 0:
        flash("Sets and reps must be greater than zero. Weight cannot be negative.", "error")
        return redirect(url_for("dashboard"))

    users = load_users()
    for stored_user in users:
        if stored_user["username"] == user["username"]:
            stored_user.setdefault("workouts", []).append(
                {
                    "id": uuid4().hex,
                    "exercise": exercise,
                    "sets": sets_count,
                    "reps": reps_count,
                    "weight": weight_amount,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            break

    save_users(users)
    flash("Workout added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/workouts/<workout_id>/delete", methods=["POST"])
def delete_workout(workout_id):
    user = require_user()
    if not user:
        return redirect(url_for("login"))

    users = load_users()
    for stored_user in users:
        if stored_user["username"] == user["username"]:
            stored_user["workouts"] = [
                workout
                for workout in stored_user.get("workouts", [])
                if workout.get("id") != workout_id
            ]
            break

    save_users(users)
    flash("Workout deleted.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
