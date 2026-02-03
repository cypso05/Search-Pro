# routes/jobs.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models.job import Job, SavedJob, JobApplication
from models.search import SearchHistory
import requests
from datetime import datetime, timedelta
import json
import uuid

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        
        if query:
            # Log search history for authenticated users
            if current_user.is_authenticated:
                search_log = SearchHistory(
                    user_id=current_user.id,
                    query=query,
                    filters={},
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.add(search_log)
                db.session.commit()
            
            # Search logic here (will be implemented in api.py)
            # For now, redirect to API endpoint
            return redirect(url_for('api.search_jobs', query=query, page=page))
        
        return render_template('search.html', query=query)
    
    # POST request from form
    query = request.form.get('query', '')
    return redirect(url_for('jobs.search', q=query))

@jobs_bp.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    is_saved = False
    
    if current_user.is_authenticated:
        saved_job = SavedJob.query.filter_by(
            user_id=current_user.id, 
            job_id=job_id
        ).first()
        is_saved = saved_job is not None
    
    return render_template('job_detail.html', job=job, is_saved=is_saved)

@jobs_bp.route('/save-job/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    saved_job = SavedJob.query.filter_by(
        user_id=current_user.id,
        job_id=job_id
    ).first()
    
    if saved_job:
        db.session.delete(saved_job)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'unsaved',
            'message': 'Job removed from saved list'
        })
    else:
        saved_job = SavedJob(
            user_id=current_user.id,
            job_id=job_id,
            notes=request.json.get('notes', '') if request.is_json else ''
        )
        db.session.add(saved_job)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'saved',
            'message': 'Job saved successfully',
            'saved_job': saved_job.to_dict()
        })

@jobs_bp.route('/saved-jobs')
@login_required
def saved_jobs():
    page = int(request.args.get('page', 1))
    per_page = 20
    status = request.args.get('status', 'all')
    
    query = SavedJob.query.filter_by(user_id=current_user.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    saved_jobs_pagination = query.order_by(
        SavedJob.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'saved_jobs.html',
        saved_jobs=saved_jobs_pagination.items,
        pagination=saved_jobs_pagination,
        status=status
    )

@jobs_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter', '')
        resume_url = request.form.get('resume_url', '')
        
        # Check if already applied
        existing_application = JobApplication.query.filter_by(
            user_id=current_user.id,
            job_id=job_id
        ).first()
        
        if existing_application:
            flash('You have already applied for this job', 'warning')
            return redirect(url_for('jobs.job_detail', job_id=job_id))
        
        # Create application
        application = JobApplication(
            user_id=current_user.id,
            job_id=job_id,
            cover_letter=cover_letter,
            resume_url=resume_url,
            status='applied',
            notes=request.form.get('notes', '')
        )
        
        db.session.add(application)
        
        # Update saved job status if exists
        saved_job = SavedJob.query.filter_by(
            user_id=current_user.id,
            job_id=job_id
        ).first()
        
        if saved_job:
            saved_job.status = 'applied'
            saved_job.applied_date = datetime.utcnow()
        
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('jobs.applications'))
    
    return render_template('apply_job.html', job=job)

@jobs_bp.route('/applications')
@login_required
def applications():
    page = int(request.args.get('page', 1))
    per_page = 20
    status = request.args.get('status', 'all')
    
    query = JobApplication.query.filter_by(user_id=current_user.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    applications_pagination = query.order_by(
        JobApplication.applied_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'applications.html',
        applications=applications_pagination.items,
        pagination=applications_pagination,
        status=status
    )

@jobs_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user stats
    total_saved = SavedJob.query.filter_by(user_id=current_user.id).count()
    total_applied = JobApplication.query.filter_by(user_id=current_user.id).count()
    
    # Get recent saved jobs
    recent_saved = SavedJob.query.filter_by(
        user_id=current_user.id
    ).order_by(
        SavedJob.created_at.desc()
    ).limit(5).all()
    
    # Get recent applications
    recent_applications = JobApplication.query.filter_by(
        user_id=current_user.id
    ).order_by(
        JobApplication.applied_date.desc()
    ).limit(5).all()
    
    # Get search history
    recent_searches = SearchHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(
        SearchHistory.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'dashboard.html',
        total_saved=total_saved,
        total_applied=total_applied,
        recent_saved=recent_saved,
        recent_applications=recent_applications,
        recent_searches=recent_searches
    )