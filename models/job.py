# models/job.py
from datetime import datetime
from app import db

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(200), index=True)
    company_logo = db.Column(db.String(500))
    location = db.Column(db.String(200))
    job_type = db.Column(db.String(50))  # full-time, part-time, contract, etc.
    experience_level = db.Column(db.String(50))  # entry, mid, senior, executive
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(10), default='USD')
    salary_period = db.Column(db.String(20), default='yearly')  # yearly, monthly, hourly
    description = db.Column(db.Text)
    requirements = db.Column(db.Text)
    benefits = db.Column(db.Text)
    remote = db.Column(db.Boolean, default=False)
    apply_url = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(50))  # rapidapi, indeed, linkedin, etc.
    source_url = db.Column(db.String(500))
    posted_date = db.Column(db.DateTime)
    expires_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    saved_by = db.relationship('SavedJob', back_populates='job', cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', back_populates='job', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('ix_jobs_title_company', 'title', 'company'),
        db.Index('ix_jobs_location', 'location'),
        db.Index('ix_jobs_posted_date', 'posted_date'),
        db.Index('ix_jobs_salary_range', 'salary_min', 'salary_max'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'company': self.company,
            'company_logo': self.company_logo,
            'location': self.location,
            'job_type': self.job_type,
            'experience_level': self.experience_level,
            'salary': {
                'min': self.salary_min,
                'max': self.salary_max,
                'currency': self.salary_currency,
                'period': self.salary_period
            } if self.salary_min or self.salary_max else None,
            'description': self.description,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'remote': self.remote,
            'apply_url': self.apply_url,
            'source': self.source,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'expires_date': self.expires_date.isoformat() if self.expires_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='interested')  # interested, applied, interviewing, offer, rejected
    applied_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='saved_jobs')
    job = db.relationship('Job', back_populates='saved_by')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='unique_user_job'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job': self.job.to_dict() if self.job else None,
            'notes': self.notes,
            'status': self.status,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    cover_letter = db.Column(db.Text)
    resume_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='applied')  # applied, reviewed, interviewing, offer, rejected
    notes = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='applications')
    job = db.relationship('Job', back_populates='applications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job': self.job.to_dict() if self.job else None,
            'cover_letter': self.cover_letter,
            'resume_url': self.resume_url,
            'status': self.status,
            'notes': self.notes,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None
        }