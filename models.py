# models.py
from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY

# ==========================
# USERS
# ==========================
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # "admin", "worker", "contractor"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    worker = db.relationship('Worker', backref='user', uselist=False)
    contractor = db.relationship('Contractor', backref='user', uselist=False)


# ==========================
# WORKERS
# ==========================
class Worker(db.Model):
    __tablename__ = 'workers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text)
    skills = db.Column(ARRAY(db.String))  # e.g., ['roofing','painting']
    availability = db.Column(db.Boolean, default=True)

    applications = db.relationship('JobApplication', backref='worker')


# ==========================
# CONTRACTORS
# ==========================
class Contractor(db.Model):
    __tablename__ = 'contractors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    business_name = db.Column(db.String(255))
    contact_info = db.Column(db.Text)

    jobs = db.relationship('Job', backref='contractor')


# ==========================
# JOBS
# ==========================
class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey('contractors.id', ondelete='CASCADE'))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='open')  # open, filled, closed

    applications = db.relationship('JobApplication', backref='job')


# ==========================
# JOB APPLICATIONS
# ==========================
class JobApplication(db.Model):
    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'))
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id', ondelete='CASCADE'))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected
