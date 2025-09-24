# models.py
from extensions import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY

# ------------------------
# USERS
# ------------------------
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # worker, contractor, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    worker = db.relationship('Worker', backref='user', uselist=False)
    contractor = db.relationship('Contractor', backref='user', uselist=False)


# ------------------------
# WORKERS
# ------------------------
class Worker(db.Model):
    __tablename__ = 'workers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    location = db.Column(db.String(255))
    skills = db.Column(ARRAY(db.String))  # list of skills
    transportation = db.Column(db.String(50))  # own vehicle, public transit, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Applications
    applications = db.relationship('JobApplication', backref='worker')


# ------------------------
# CONTRACTORS
# ------------------------
class Contractor(db.Model):
    __tablename__ = 'contractors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    business_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Posted jobs
    jobs = db.relationship('Job', backref='contractor')


# ------------------------
# JOBS
# ------------------------
class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255))
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id'), nullable=False)
    required_skills = db.Column(ARRAY(db.String))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Applications
    applications = db.relationship('JobApplication', backref='job')


# ------------------------
# JOB APPLICATIONS
# ------------------------
class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
