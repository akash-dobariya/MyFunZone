from flask import Blueprint, render_template, request, redirect, url_for, flash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # temporary check
        if email == "admin@funzone.com" and password == "admin":
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")


@auth_bp.route("/dashboard")
def dashboard():
    return "✅ Login Successful"
