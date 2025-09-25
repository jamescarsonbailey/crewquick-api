# routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, get_jwt
)
from flask_cors import cross_origin  # ✅ CORS per-route
from extensions import db
from models import User, Worker, Contractor, Job, JobApplication
import os

bp = Blueprint("api", __name__)

# Configure allowed origin(s) for CORS.
# In prod, set FRONTEND_ORIGIN=https://yourapp.vercel.app
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
CORS_KW = dict(
    origins=FRONTEND_ORIGIN,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    supports_credentials=False,  # set True if you later use cookies
    max_age=86400,  # cache preflight for a day
)

def require_fields(data, *fields):
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return {"error": f"Missing fields: {', '.join(missing)}"}, 400
    return None

# ----------------------
# SIGNUP
# ----------------------
@bp.route("/signup", methods=["POST", "OPTIONS"])
@cross_origin(**CORS_KW)
def signup():
    data = request.get_json() or {}
    guard = require_fields(data, "email", "password", "role")
    if guard: return jsonify(guard[0]), guard[1]

    email = data["email"]
    password = data["password"]
    role = data["role"]  # "worker" or "contractor"

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    user = User(email=email, password_hash=generate_password_hash(password), role=role)
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
@bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin(**CORS_KW)
def login():
    data = request.get_json() or {}
    guard = require_fields(data, "email", "password")
    if guard: return jsonify(guard[0]), guard[1]

    email = data["email"]
    password = data["password"]

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),                  # JWT "sub" must be a string
        additional_claims={"role": user.role}  # role available via get_jwt()["role"]
    )
    return jsonify({"access_token": access_token, "user_id": user.id, "role": user.role})

# ----------------------
# POST A JOB (Contractor)
# ----------------------
@bp.route("/jobs", methods=["POST", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def post_job():
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "contractor":
        return jsonify({"error": "Only contractors can post jobs"}), 403

    data = request.get_json() or {}
    guard = require_fields(data, "title", "description", "location")
    if guard: return jsonify(guard[0]), guard[1]

    job = Job(
        title=data["title"],
        description=data["description"],
        location=data["location"],
        contractor_id=user_id,
        required_skills=data.get("required_skills")
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully", "job_id": job.id})

# ----------------------
# LIST ALL JOBS (Workers/Contractors)
# ----------------------
@bp.route("/jobs", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def list_jobs():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "location": j.location,
        "contractor_id": j.contractor_id,
        "required_skills": j.required_skills,
        "created_at": j.created_at.isoformat() if j.created_at else None
    } for j in jobs])

# ----------------------
# APPLY TO JOB (Worker)
# ----------------------
@bp.route("/jobs/<int:job_id>/apply", methods=["POST", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def apply_job(job_id):
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "worker":
        return jsonify({"error": "Only workers can apply to jobs"}), 403

    # Map user -> worker
    worker = Worker.query.filter_by(user_id=user_id).first()
    if not worker:
        return jsonify({"error": "Worker profile not found"}), 404

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    existing = JobApplication.query.filter_by(worker_id=worker.id, job_id=job_id).first()
    if existing:
        return jsonify({"error": "Already applied to this job"}), 400

    application = JobApplication(worker_id=worker.id, job_id=job_id)
    db.session.add(application)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully"})


# ----------------------
# ADMIN: LIST USERS
# ----------------------
@bp.route("/admin/users", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def list_users():
    role = get_jwt()["role"]
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.order_by(User.id.asc()).all()
    return jsonify([{"id": u.id, "email": u.email, "role": u.role} for u in users])

# ----------------------
# ADMIN: LIST JOBS
# ----------------------
@bp.route("/admin/jobs", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def list_jobs_admin():
    role = get_jwt()["role"]
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id": j.id,
        "title": j.title,
        "description": j.description,
        "location": j.location,
        "contractor_id": j.contractor_id,
        "required_skills": j.required_skills,
        "created_at": j.created_at.isoformat() if j.created_at else None
    } for j in jobs])

@bp.route("/me", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    u = User.query.get(user_id)
    base = {"id": u.id, "email": u.email, "role": u.role}

    if role == "worker":
        w = Worker.query.filter_by(user_id=user_id).first()
        base["profile"] = {
            "name": w.name if w else None,
            "location": w.location if w else None,
            "skills": w.skills if w else None,
            "transportation": w.transportation if w else None,
        }
    elif role == "contractor":
        c = Contractor.query.filter_by(user_id=user_id).first()
        base["profile"] = {
            "business_name": c.business_name if c else None,
            "location": c.location if c else None,
            "phone": c.phone if c else None,
        }
    return jsonify(base)

@bp.route("/me/applications", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def my_applications():
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "worker":
        return jsonify({"error": "Worker role required"}), 403

    worker = Worker.query.filter_by(user_id=user_id).first()
    if not worker:
        return jsonify({"error": "Worker profile not found"}), 404

    apps = (JobApplication.query
            .filter_by(worker_id=worker.id)
            .join(Job, Job.id == JobApplication.job_id)
            .order_by(JobApplication.applied_at.desc())
            .all())

    return jsonify([{
        "application_id": a.id,
        "job_id": a.job_id,
        "applied_at": a.applied_at.isoformat() if a.applied_at else None,
        "job": {
            "title": a.job.title,
            "location": a.job.location,
            "contractor_id": a.job.contractor_id
        }
    } for a in apps])



@bp.route("/me/jobs", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def my_jobs():
    user_id = int(get_jwt_identity())
    role = get_jwt()["role"]
    if role != "contractor":
        return jsonify({"error": "Contractor role required"}), 403

    jobs = Job.query.filter_by(contractor_id=user_id).order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id": j.id, "title": j.title, "description": j.description,
        "location": j.location, "required_skills": j.required_skills,
        "created_at": j.created_at.isoformat() if j.created_at else None
    } for j in jobs])


@bp.route("/jobs", methods=["GET", "OPTIONS"])
@cross_origin(**CORS_KW)
@jwt_required()
def list_jobs():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    q = Job.query.order_by(Job.created_at.desc())
    items = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "results": [{
            "id": j.id, "title": j.title, "description": j.description,
            "location": j.location, "contractor_id": j.contractor_id,
            "required_skills": j.required_skills,
            "created_at": j.created_at.isoformat() if j.created_at else None
        } for j in items.items],
        "page": page, "per_page": per_page, "total": items.total
    })
