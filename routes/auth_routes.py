from flask import Blueprint, request, redirect, session, url_for, render_template, flash, jsonify
from models import Worker, Company
from database import db
import secrets

auth_bp = Blueprint('auth_bp', __name__)

# NOTE: You may need to import global objects like 'google' depending on setup
@auth_bp.route('/login/google')
def login_google():
    role = request.args.get("role")   # worker or company
    session["oauth_role"] = role
    redirect_uri = url_for('auth_bp.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)



@auth_bp.route('/login/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("userinfo").json()

    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("id")

    role = session.get("oauth_role")   # worker / company
    temp_password = secrets.token_urlsafe(16)

    if role == "company":
        user = Company.query.filter_by(email=email).first()
        if not user:
            user = Company(
                company_name=name,
                email=email,
                google_id=google_id,
                password=temp_password,
                is_password_set=False
            )
            db.session.add(user)
            db.session.commit()

        session.clear()
        session["company_id"] = user.id
        session["user_type"] = "company"

        if not user.is_password_set:
            return redirect(url_for("auth_bp.set_company_password"))

        return redirect(url_for("companyprofile"))

    # -------- WORKER --------
    user = Worker.query.filter_by(email=email).first()
    if not user:
        user = Worker(
            name=name,
            email=email,
            google_id=google_id,
            password=temp_password,
            is_password_set=False
        )
        db.session.add(user)
        db.session.commit()

    session.clear()
    session["worker_id"] = user.id
    session["user_type"] = "worker"

    if not user.is_password_set:
        return redirect(url_for("auth_bp.set_password"))

    return redirect(url_for("workerprofile"))


@auth_bp.route("/set-password", methods=["GET","POST"])
def set_password():
    if request.method == "POST":
        pwd = request.form["password"]
        
        user = Worker.query.get(session["worker_id"])
        user.password = pwd
        user.is_password_set = True
        db.session.commit()
        return redirect(url_for("workerprofile"))
    return render_template("set_password.html")


@auth_bp.route("/set-company-password", methods=["GET","POST"])
def set_company_password():
    if "company_id" not in session:
        return redirect(url_for("auth_bp.login"))

    if request.method == "POST":
        pwd = request.form["password"]
        company = Company.query.get(session["company_id"])
        company.password = pwd
        company.is_password_set = True
        db.session.commit()
        return redirect(url_for("companyprofile"))

    return render_template("set_password.html")


@auth_bp.route("/forgot-password")
def forgot_password():
    flash("Please contact support to recover your password.", "warning")
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/login')
def login():
    return render_template('login.html')


@auth_bp.route("/login/worker", methods=["POST"])
def login_worker():
    email = request.form.get("mail")
    password = request.form.get("password")

    if not email or not password:
        flash("All fields are required", "error")
        return redirect(url_for("auth_bp.login"))

    worker = Worker.query.filter_by(email=email).first()

    if not worker or worker.password != password:
        flash("Invalid phone number or password", "error")
        return redirect(url_for("auth_bp.login"))

    session.clear()
    session["worker_id"] = worker.id
    session["user_type"] = "worker"

    return redirect(url_for("workerprofile"))


@auth_bp.route("/login/company", methods=["POST"])
def login_company():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("All fields are required", "error")
        return redirect(url_for("auth_bp.login"))

    company = Company.query.filter_by(email=email).first()

    if not company or company.password != password:
        flash("Invalid email or password", "error")
        return redirect(url_for("auth_bp.login"))

    session.clear()
    session["company_id"] = company.id
    session["user_type"] = "company"

    return redirect(url_for("companyprofile"))

# ======================== WORKER =========================

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


