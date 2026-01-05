from flask import Blueprint, render_template, request, redirect, url_for, session
from app.src import db
from app.src.models.user import User

auth_bp = Blueprint("auth", __name__)


# -------- Helper: role based redirect --------
def get_home_route(role):
    if role == "admin":
        return url_for("auth.admin_home")
    elif role == "staff":
        return url_for("auth.staff_home")
    return url_for("auth.user_home")


# ---------------- REGISTER ----------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            return "Email already exists"

        user = User(
            name=name,
            email=email,
            password=password,
            role="user"
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # already logged in
    if session.get("user_role"):
        return redirect(get_home_route(session["user_role"]))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()
        if not user:
            return "Invalid email or password"

        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_role"] = user.role

        return redirect(get_home_route(user.role))

    return render_template("login.html")


# ---------------- USER HOME ----------------
@auth_bp.route("/user/home")
def user_home():
    if session.get("user_role") != "user":
        return redirect(url_for("auth.login"))
    return render_template("home_user.html")


# ---------------- ADMIN HOME ----------------
@auth_bp.route("/admin/home")
def admin_home():
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.login"))
    return render_template("home_admin.html")


# ---------------- STAFF HOME ----------------
@auth_bp.route("/staff/home")
def staff_home():
    if session.get("user_role") != "staff":
        return redirect(url_for("auth.login"))
    return render_template("home_staff.html")


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
