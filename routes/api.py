# routes/api.py
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db, celery
from models.job import Job, SavedJob
from models.search import SearchHistory
import requests
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy import or_

api_bp = Blueprint('api', __name__)

# API Rate limiting decorator (simplified)
def rate_limit(key='ip', limit=100, period=3600):
    """Simple rate limiting decorator"""
    # In production, use Flask-Limiter or Redis
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Implement rate limiting logic here
            return f(*args, **kwargs)
        return wrapper
    return decorator

@api_bp.route('/search', methods=['GET'])
@rate_limit(limit=50, period=3600)
def search_jobs():
    """Search jobs from multiple sources"""
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Parse filters
    filters = {
        'location': request.args.get('location', ''),
        'job_type': request.args.get('job_type', ''),
        'experience': request.args.get('experience', ''),
        'remote': request.args.get('remote', 'false').lower() == 'true',
        'salary_min': request.args.get('salary_min', type=int),
        'salary_max': request.args.get('salary_max', type=int)
    }
    
    # Check cache first
    cache_key = f"search:{query}:{json.dumps(filters, sort_keys=True)}:{page}"
    # Implement caching with Redis in production
    
    try:
        # Search local database first
        local_results = search_local_jobs(query, filters, page, per_page)
        
        # If insufficient local results, fetch from external APIs
        if len(local_results['jobs']) < per_page:
            external_results = fetch_external_jobs(query, filters, page, per_page)
            # Merge and deduplicate results
            all_results = merge_job_results(local_results['jobs'], external_results)
        else:
            all_results = local_results['jobs']
        
        # Log search for authenticated users
        if current_user.is_authenticated:
            search_log = SearchHistory(
                user_id=current_user.id,
                query=query,
                filters=filters,
                result_count=len(all_results),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(search_log)
            db.session.commit()
        
        # Paginate results
        total = len(all_results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = all_results[start:end]
        
        return jsonify({
            'success': True,
            'query': query,
            'filters': filters,
            'jobs': paginated_results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

def search_local_jobs(query, filters, page, per_page):
    """Search jobs from local database"""
    # Build search query
    search_query = Job.query.filter(Job.is_active == True)
    
    # Full-text search on title and description
    if query:
        search_terms = query.split()
        for term in search_terms:
            search_query = search_query.filter(
                or_(
                    Job.title.ilike(f'%{term}%'),
                    Job.description.ilike(f'%{term}%'),
                    Job.company.ilike(f'%{term}%')
                )
            )
    
    # Apply filters
    if filters.get('location'):
        search_query = search_query.filter(Job.location.ilike(f'%{filters["location"]}%'))
    
    if filters.get('job_type'):
        search_query = search_query.filter(Job.job_type == filters['job_type'])
    
    if filters.get('experience'):
        search_query = search_query.filter(Job.experience_level == filters['experience'])
    
    if filters.get('remote'):
        search_query = search_query.filter(Job.remote == True)
    
    if filters.get('salary_min'):
        search_query = search_query.filter(Job.salary_max >= filters['salary_min'])
    
    if filters.get('salary_max'):
        search_query = search_query.filter(Job.salary_min <= filters['salary_max'])
    
    # Get total count
    total = search_query.count()
    
    # Paginate
    jobs = search_query.order_by(Job.posted_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return {
        'jobs': [job.to_dict() for job in jobs.items],
        'total': total
    }

def fetch_external_jobs(query, filters, page, per_page):
    """Fetch jobs from external APIs"""
    jobs = []
    config = current_app.config
    
    try:
        # RapidAPI
        if config.get('RAPID_API_KEY'):
            headers = {
                "X-RapidAPI-Key": config['RAPID_API_KEY'],
                "X-RapidAPI-Host": config['RAPID_API_HOST']
            }
            
            params = {
                "q": f"{query} job {filters.get('location', '')}",
                "limit": str(per_page * 2)  # Fetch extra for filtering
            }
            
            response = requests.get(
                "https://real-time-web-search.p.rapidapi.com/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for item in data['data']:
                        job = parse_external_job(item, 'rapidapi')
                        if job and matches_filters(job, filters):
                            jobs.append(job)
        
        # Add more API sources here (Indeed, LinkedIn, etc.)
        
    except Exception as e:
        current_app.logger.error(f"External API error: {str(e)}")
    
    return jobs

def parse_external_job(data, source):
    """Parse external API response into Job object"""
    try:
        # Generate unique external ID
        external_id = f"{source}:{data.get('url', str(uuid.uuid4()))}"
        
        job = Job(
            external_id=external_id,
            title=data.get('title', ''),
            company=extract_company(data),
            location=extract_location(data),
            description=data.get('snippet', data.get('description', '')),
            apply_url=data.get('url', data.get('link', '')),
            source=source,
            source_url=data.get('url', ''),
            posted_date=extract_posted_date(data),
            created_at=datetime.utcnow()
        )
        
        # Try to extract salary if available
        salary_info = extract_salary(data)
        if salary_info:
            job.salary_min = salary_info.get('min')
            job.salary_max = salary_info.get('max')
            job.salary_currency = salary_info.get('currency', 'USD')
            job.salary_period = salary_info.get('period', 'yearly')
        
        # Try to extract job type and experience
        job.job_type = extract_job_type(data)
        job.experience_level = extract_experience_level(data)
        
        # Check if remote
        job.remote = is_remote_job(data, job.title, job.description)
        
        return job
        
    except Exception as e:
        current_app.logger.error(f"Error parsing job: {str(e)}")
        return None

def matches_filters(job, filters):
    """Check if job matches given filters"""
    if filters.get('location') and job.location:
        if filters['location'].lower() not in job.location.lower():
            return False
    
    if filters.get('job_type') and job.job_type:
        if filters['job_type'] != job.job_type:
            return False
    
    if filters.get('experience') and job.experience_level:
        if filters['experience'] != job.experience_level:
            return False
    
    if filters.get('remote') and not job.remote:
        return False
    
    if filters.get('salary_min') and job.salary_max:
        if job.salary_max < filters['salary_min']:
            return False
    
    if filters.get('salary_max') and job.salary_min:
        if job.salary_min > filters['salary_max']:
            return False
    
    return True

def extract_company(data):
    """Extract company name from various data formats"""
    return data.get('company', data.get('domain', data.get('source', '')))

def extract_location(data):
    """Extract location from various data formats"""
    return data.get('location', '')

def extract_posted_date(data):
    """Extract posted date from various data formats"""
    # Implementation depends on API response format
    return datetime.utcnow()

def extract_salary(data):
    """Extract salary information"""
    # Implementation depends on API response format
    return None

def extract_job_type(data):
    """Extract job type from title/description"""
    title = data.get('title', '').lower()
    description = data.get('snippet', '').lower()
    
    if any(term in title or term in description for term in ['full-time', 'full time']):
        return 'full-time'
    elif any(term in title or term in description for term in ['part-time', 'part time']):
        return 'part-time'
    elif any(term in title or term in description for term in ['contract', 'freelance']):
        return 'contract'
    elif any(term in title or term in description for term in ['intern', 'internship']):
        return 'internship'
    
    return None

def extract_experience_level(data):
    """Extract experience level from title/description"""
    title = data.get('title', '').lower()
    description = data.get('snippet', '').lower()
    
    if any(term in title or term in description for term in ['senior', 'sr.', 'lead', 'principal']):
        return 'senior'
    elif any(term in title or term in description for term in ['mid-level', 'mid level', 'mid']):
        return 'mid'
    elif any(term in title or term in description for term in ['junior', 'entry-level', 'entry level', 'associate']):
        return 'entry'
    elif any(term in title or term in description for term in ['executive', 'director', 'vp', 'c-level']):
        return 'executive'
    
    return None

def is_remote_job(data, title, description):
    """Check if job is remote"""
    text = f"{title} {description}".lower()
    remote_keywords = ['remote', 'work from home', 'wfh', 'virtual', 'telecommute']
    return any(keyword in text for keyword in remote_keywords)

def merge_job_results(local_jobs, external_jobs):
    """Merge and deduplicate job results"""
    seen_urls = set()
    all_jobs = []
    
    # Add local jobs
    for job_dict in local_jobs:
        if isinstance(job_dict, dict) and job_dict.get('apply_url'):
            seen_urls.add(job_dict['apply_url'])
            all_jobs.append(job_dict)
    
    # Add external jobs (skip duplicates)
    for job in external_jobs:
        if isinstance(job, Job) and job.apply_url not in seen_urls:
            seen_urls.add(job.apply_url)
            all_jobs.append(job.to_dict())
    
    return all_jobs

@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get job details"""
    job = Job.query.get_or_404(job_id)
    return jsonify({'success': True, 'job': job.to_dict()})

@api_bp.route('/jobs/save', methods=['POST'])
@login_required
def save_job_api():
    """Save a job for current user"""
    data = request.get_json()
    job_id = data.get('job_id')
    
    if not job_id:
        return jsonify({'error': 'Job ID is required'}), 400
    
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
    
    saved_job = SavedJob(
        user_id=current_user.id,
        job_id=job_id,
        notes=data.get('notes', ''),
        status=data.get('status', 'interested')
    )
    
    db.session.add(saved_job)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': 'saved',
        'message': 'Job saved successfully',
        'saved_job': saved_job.to_dict()
    })

@api_bp.route('/jobs/saved', methods=['GET'])
@login_required
def get_saved_jobs():
    """Get saved jobs for current user"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status = request.args.get('status', 'all')
    
    query = SavedJob.query.filter_by(user_id=current_user.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    saved_jobs = query.order_by(
        SavedJob.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'saved_jobs': [sj.to_dict() for sj in saved_jobs.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': saved_jobs.total,
            'pages': saved_jobs.pages
        }
    })

@api_bp.route('/stats/search-trends', methods=['GET'])
@login_required
def get_search_trends():
    """Get search trends for dashboard"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get popular searches
    popular_searches = db.session.query(
        SearchHistory.query,
        db.func.count(SearchHistory.id).label('count')
    ).group_by(SearchHistory.query).order_by(
        db.desc('count')
    ).limit(10).all()
    
    # Get search trends by day
    trends_by_day = db.session.query(
        db.func.date(SearchHistory.created_at).label('date'),
        db.func.count(SearchHistory.id).label('count')
    ).filter(
        SearchHistory.created_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(
        db.func.date(SearchHistory.created_at)
    ).order_by(
        db.func.date(SearchHistory.created_at)
    ).all()
    
    return jsonify({
        'success': True,
        'popular_searches': [
            {'query': item[0], 'count': item[1]} 
            for item in popular_searches
        ],
        'trends_by_day': [
            {'date': item[0].isoformat(), 'count': item[1]}
            for item in trends_by_day
        ]
    })