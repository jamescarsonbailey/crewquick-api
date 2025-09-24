# routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, get_jwt
)
from extensions import db
from models import User, Worker, Contractor, Job, JobApplication

# ----------------------
# Create Blueprint
# ----------------------
bp = Blueprint("api", __name__)

# ----------------------
# SIGNUP
# ----------------------
@bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")  # "worker" or "contractor"

    if not email or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    user = User(email=email, password_hash=hashed_password, role=role)
    db.session.add(user)
    db.session.commit()

    # Role-specific record
    if role == "worker":
        worker = Worker(user_id=user.id, name=data.get("name"))
        db.session.add(worker)
    elif role == "contractor":
        contractor = Contractor(user_id=user.id, business_name=data.get("business_name"))
        db.session.add(contractor)
    else:
        return jsonify({"error": "Invalid role"}), 400

    db.session.commit()
    return jsonify({"message": f"{role.capitalize()} signed up successfully", "user_id": user.id})

# ----------------------
# LOGIN
# ----------------------
@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),           # must be string
        additional_claims={"role": user.role}
    )

    return jsonify({"access_token": access_token, "user_id": user.id, "role": user.role})

# ----------------------
# POST A JOB (Contractor)
# ----------------------
@bp.route("/jobs", methods=["POST"])
@jwt_required()
def post_job():
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]

    if role != "contractor":
        return jsonify({"error": "Only contractors can post jobs"}), 403

    data = request.get_json()
    job = Job(
        title=data.get("title"),
        description=data.get("description"),
        location=data.get("location"),
        contractor_id=user_id,
        required_skills=data.get("required_skills")
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully", "job_id": job.id})

# ----------------------
# LIST ALL JOBS (Workers)
# ----------------------
@bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    jobs = Job.query.all()
    jobs_list = []
    for j in jobs:
        jobs_list.append({
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "contractor_id": j.contractor_id,
            "required_skills": j.required_skills
        })
    return jsonify(jobs_list)

# ----------------------
# APPLY TO JOB (Worker)
# ----------------------
@bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
@jwt_required()
def apply_job(job_id):
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]

    if role != "worker":
        return jsonify({"error": "Only workers can apply to jobs"}), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    existing_application = JobApplication.query.filter_by(worker_id=user_id, job_id=job_id).first()
    if existing_application:
        return jsonify({"error": "Already applied to this job"}), 400

    application = JobApplication(worker_id=user_id, job_id=job_id)
    db.session.add(application)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully"})

# ----------------------
# ADMIN: LIST USERS
# ----------------------
@bp.route("/admin/users", methods=["GET"])
@jwt_required()
def list_users():
    role = get_jwt()["role"]
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.all()
    user_list = [{"id": u.id, "email": u.email, "role": u.role} for u in users]
    return jsonify(user_list)

# ----------------------
# ADMIN: LIST JOBS
# ----------------------
@bp.route("/admin/jobs", methods=["GET"])
@jwt_required()
def list_jobs_admin():
    role = get_jwt()["role"]
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    jobs = Job.query.all()
    job_list = [{
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "location": j.location,
        "contractor_id": j.contractor_id,
        "required_skills": j.required_skills
    } for j in jobs]
    return jsonify(job_list)
