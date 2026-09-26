from flask import Blueprint, render_template, request
from models import JobPost

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    jobs = JobPost.query.order_by(JobPost.created_at.desc()).limit(6).all()
    return render_template("home.html", jobs=jobs)

import os

@main_bp.route("/industry-map")
def industrymap():
    search_query = request.args.get("search", "")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    return render_template("industrymap.html", search_query=search_query, api_key=api_key)

@main_bp.route('/product_view')
def productview():
    return render_template('product_view.html')
