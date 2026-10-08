from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name= db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name= db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    resume = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    projects = db.Column(db.Integer, default=0, nullable=True)
    backlogs = db.Column(db.Integer, default=0, nullable=True)
    aptitude_score = db.Column(db.Float, default=None, nullable=True)
    internships = db.Column(db.Integer, default=0, nullable=True)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    approval_status = db.Column(db.String(20), default='pending')

class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    package = db.Column(db.String(50))
    location = db.Column(db.String(100))
    deadline = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    min_cgpa = db.Column(db.Float, default=None, nullable=True)
    max_backlogs = db.Column(db.Integer, default=99, nullable=True)
    preferred_streams = db.Column(db.Text, default=None, nullable=True)
    required_skills = db.Column(db.Text, default=None, nullable=True)
    min_projects = db.Column(db.Integer, default=0, nullable=True)
    min_internships = db.Column(db.Integer, default=0, nullable=True)



class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    status = db.Column(db.String(20), default='Applied')

