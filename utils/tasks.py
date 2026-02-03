import os
import json
import time
from datetime import datetime, timedelta
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# ============================================================================
# ENVIRONMENT DETECTION & CONFIGURATION
# ============================================================================

# Detect if running on PythonAnywhere
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ

# ============================================================================
# DATABASE HELPER (Avoids circular imports)
# ============================================================================

def get_db_session():
    """Get database session without circular imports"""
    try:
        # Import here to avoid circular imports
        from app import create_app, db
        app = create_app()
        with app.app_context():
            return db.session
    except Exception as e:
        print(f"❌ Error getting database session: {e}")
        # Fallback: Create a direct connection
        try:
            from Config import Config
            engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
            Session = scoped_session(sessionmaker(bind=engine))
            return Session()
        except:
            raise Exception("Could not establish database connection")

def get_app_config():
    """Get app config without circular imports"""
    try:
        from app import create_app
        app = create_app()
        return app.config
    except:
        # Fallback for PythonAnywhere
        from Config import Config
        return {
            'RAPID_API_KEY': os.getenv('RAPID_API_KEY'),
            'RAPID_API_HOST': os.getenv('RAPID_API_HOST', 'real-time-web-search.p.rapidapi.com')
        }

# ============================================================================
# TASK EXECUTION HELPER
# ============================================================================

def run_background_task(task_func, *args, **kwargs):
    """
    Run tasks appropriately for the environment
    
    Args:
        task_func: The task function to run
        *args: Arguments to pass to the task
        **kwargs: Keyword arguments to pass to the task
    
    Returns:
        Task result or Celery AsyncResult
    """
    if IS_PYTHONANYWHERE:
        # PythonAnywhere: Run synchronously
        print(f"📋 Running task synchronously on PythonAnywhere: {task_func.__name__}")
        try:
            result = task_func(*args, **kwargs)
            print(f"✅ Task completed: {task_func.__name__}")
            return {
                'success': True,
                'result': result,
                'async': False,
                'environment': 'pythonanywhere'
            }
        except Exception as e:
            print(f"❌ Task failed on PythonAnywhere: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'async': False,
                'environment': 'pythonanywhere'
            }
    else:
        # Local/Production: Use Celery
        print(f"🚀 Queueing Celery task: {task_func.__name__}")
        try:
            if hasattr(task_func, 'delay'):
                # It's a Celery task
                async_result = task_func.delay(*args, **kwargs)
                return {
                    'success': True,
                    'task_id': async_result.id,
                    'async': True,
                    'environment': 'local/production'
                }
            else:
                # Fallback to synchronous if not a Celery task
                result = task_func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'async': False,
                    'environment': 'local/production'
                }
        except Exception as e:
            print(f"❌ Failed to queue Celery task: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'async': False,
                'environment': 'local/production'
            }

# ============================================================================
# CELERY SETUP (Only for non-PythonAnywhere environments)
# ============================================================================

if not IS_PYTHONANYWHERE:
    from celery import Celery
    
    def make_celery(app):
        """Create Celery instance with Flask app context"""
        celery = Celery(
            app.import_name,
            backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
            broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        )
        
        # Update Celery config from Flask app
        celery.conf.update(app.config)
        
        # Task execution within Flask app context
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
        return celery
    
    # Import Flask app creation function
    try:
        from app import create_app
        app = create_app()
        celery = make_celery(app)
    except Exception as e:
        print(f"⚠️  Could not create Celery app: {e}")
        # Create a minimal Celery instance for fallback
        celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
    
    # Decorator to mark functions as Celery tasks
    def celery_task(name=None):
        """Decorator to make a function a Celery task"""
        def decorator(func):
            if IS_PYTHONANYWHERE:
                # On PythonAnywhere, just return the function as-is
                return func
            else:
                # On local/production, wrap with Celery
                return celery.task(name=name)(func)
        return decorator
else:
    # On PythonAnywhere, create a dummy decorator
    def celery_task(name=None):
        """Dummy decorator for PythonAnywhere"""
        def decorator(func):
            # Just return the function as-is
            func.is_celery_task = False
            func.task_name = name or func.__name__
            return func
        return decorator

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def fetch_job_details(external_id, source):
    """Fetch updated job details from external source"""
    try:
        config = get_app_config()
        
        # Example: Fetch from RapidAPI
        if source == 'rapidapi' and config.get('RAPID_API_KEY'):
            headers = {
                "X-RapidAPI-Key": config['RAPID_API_KEY'],
                "X-RapidAPI-Host": config.get('RAPID_API_HOST', 'real-time-web-search.p.rapidapi.com')
            }
            
            # Placeholder implementation
            # In production, implement actual API call
            # response = requests.get(f"https://api.example.com/jobs/{external_id}", headers=headers)
            # return response.json() if response.status_code == 200 else None
            
            return None  # Placeholder
        else:
            return None
    except Exception as e:
        print(f"Error fetching job details for {external_id}: {str(e)}")
        return None

def fetch_external_jobs(keyword, filters, page, per_page):
    """Fetch jobs from external APIs"""
    jobs = []
    
    try:
        config = get_app_config()
        
        # Example implementation using RapidAPI
        if config.get('RAPID_API_KEY'):
            headers = {
                "X-RapidAPI-Key": config['RAPID_API_KEY'],
                "X-RapidAPI-Host": config.get('RAPID_API_HOST', 'real-time-web-search.p.rapidapi.com')
            }
            
            params = {
                "q": f"{keyword} job",
                "limit": str(per_page)
            }
            
            if filters.get('location'):
                params["q"] += f" {filters['location']}"
            
            response = requests.get(
                "https://real-time-web-search.p.rapidapi.com/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    # Parse job data
                    import hashlib
                    url_hash = hashlib.md5(item.get('url', '').encode()).hexdigest()
                    
                    job_data = {
                        'external_id': f"rapidapi:{url_hash}",
                        'title': item.get('title', ''),
                        'company': item.get('source', 'Unknown'),
                        'location': '',
                        'description': item.get('snippet', ''),
                        'apply_url': item.get('url', ''),
                        'source': 'rapidapi',
                        'source_url': item.get('url', ''),
                        'posted_date': datetime.utcnow()
                    }
                    jobs.append(job_data)
    
    except Exception as e:
        print(f"Error fetching external jobs: {str(e)}")
    
    return jobs

# ============================================================================
# TASK DEFINITIONS (Environment Aware)
# ============================================================================

@celery_task(name='tasks.refresh_jobs')
def refresh_jobs():
    """Background task to refresh job listings"""
    try:
        print("🔄 Starting job refresh task...")
        
        # Get database session
        from models.job import Job
        db_session = get_db_session()
        
        # Get jobs that need refreshing (older than 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        old_jobs = db_session.query(Job).filter(
            Job.updated_at < cutoff,
            Job.is_active == True
        ).limit(100).all()
        
        updated_count = 0
        deactivated_count = 0
        
        for job in old_jobs:
            try:
                # Update job details from source
                updated_job = fetch_job_details(job.external_id, job.source)
                if updated_job:
                    # Update job fields
                    job.title = updated_job.get('title', job.title)
                    job.description = updated_job.get('description', job.description)
                    job.company = updated_job.get('company', job.company)
                    job.location = updated_job.get('location', job.location)
                    job.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Mark job as inactive if it no longer exists
                    job.is_active = False
                    job.updated_at = datetime.utcnow()
                    deactivated_count += 1
                    
            except Exception as e:
                print(f"Error updating job {job.id}: {str(e)}")
                job.is_active = False
                deactivated_count += 1
        
        db_session.commit()
        db_session.close()
        
        result = {
            'success': True, 
            'updated': updated_count,
            'deactivated': deactivated_count,
            'total_processed': len(old_jobs)
        }
        
        print(f"✅ Job refresh completed: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error in refresh_jobs task: {str(e)}"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': str(e)}

@celery_task(name='tasks.fetch_new_jobs')
def fetch_new_jobs(keywords=None, max_per_keyword=50):
    """Background task to fetch new jobs for popular keywords"""
    if not keywords:
        keywords = [
            'software engineer', 'data scientist', 'web developer',
            'product manager', 'marketing', 'sales'
        ]
    
    print(f"🔍 Fetching new jobs for keywords: {keywords}")
    
    # Get database session
    from models.job import Job
    db_session = get_db_session()
    
    new_jobs_count = 0
    skipped_jobs = 0
    
    for keyword in keywords:
        try:
            # Fetch jobs for keyword
            jobs = fetch_external_jobs(keyword, {}, 1, max_per_keyword)
            
            print(f"📥 Found {len(jobs)} potential jobs for '{keyword}'")
            
            for job_data in jobs:
                try:
                    # Check if job already exists
                    existing = db_session.query(Job).filter_by(
                        external_id=job_data.get('external_id')
                    ).first()
                    
                    if not existing:
                        # Create Job object from dict
                        job = Job(
                            external_id=job_data.get('external_id'),
                            title=job_data.get('title'),
                            company=job_data.get('company'),
                            location=job_data.get('location'),
                            description=job_data.get('description'),
                            apply_url=job_data.get('apply_url'),
                            source=job_data.get('source'),
                            source_url=job_data.get('source_url'),
                            posted_date=job_data.get('posted_date'),
                            is_active=True
                        )
                        
                        db_session.add(job)
                        new_jobs_count += 1
                        
                        # Commit in batches to avoid large transactions
                        if new_jobs_count % 20 == 0:
                            db_session.commit()
                            print(f"💾 Saved {new_jobs_count} jobs so far...")
                    else:
                        skipped_jobs += 1
                        
                except Exception as e:
                    print(f"Error processing job data: {str(e)}")
                    continue
            
            # Final commit for this keyword
            db_session.commit()
            
        except Exception as e:
            print(f"Error fetching jobs for {keyword}: {str(e)}")
            db_session.rollback()
            continue
    
    db_session.close()
    
    result = {
        'success': True, 
        'new_jobs': new_jobs_count,
        'skipped_jobs': skipped_jobs,
        'keywords_processed': len(keywords)
    }
    
    print(f"✅ New job fetch completed: {result}")
    return result

@celery_task(name='tasks.cleanup_old_jobs')
def cleanup_old_jobs(days=30):
    """Clean up old inactive jobs"""
    try:
        print(f"🗑️  Cleaning up jobs older than {days} days...")
        
        # Get database session
        from models.job import Job
        db_session = get_db_session()
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Find jobs to delete
        jobs_to_delete = db_session.query(Job).filter(
            Job.is_active == False,
            Job.updated_at < cutoff
        ).all()
        
        deleted_count = len(jobs_to_delete)
        
        if deleted_count > 0:
            # Delete in batches to avoid large transactions
            batch_size = 100
            for i in range(0, deleted_count, batch_size):
                batch = jobs_to_delete[i:i+batch_size]
                for job in batch:
                    db_session.delete(job)
                
                db_session.commit()
                print(f"🧹 Deleted batch {i//batch_size + 1}: {len(batch)} jobs")
        
        db_session.close()
        
        result = {'success': True, 'deleted': deleted_count}
        print(f"✅ Cleanup completed: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error in cleanup_old_jobs: {str(e)}"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': str(e)}

# ============================================================================
# TASK SCHEDULER (Only for local/production)
# ============================================================================

if not IS_PYTHONANYWHERE:
    try:
        @celery.on_after_configure.connect
        def setup_periodic_tasks(sender, **kwargs):
            """Setup periodic tasks for Celery"""
            try:
                # Refresh jobs every 6 hours
                sender.add_periodic_task(
                    6 * 3600.0,  # 6 hours in seconds
                    refresh_jobs.s(),
                    name='Refresh job listings every 6 hours'
                )
                
                # Fetch new jobs every 12 hours
                sender.add_periodic_task(
                    12 * 3600.0,  # 12 hours in seconds
                    fetch_new_jobs.s(),
                    name='Fetch new jobs every 12 hours'
                )
                
                # Cleanup old jobs every day
                sender.add_periodic_task(
                    24 * 3600.0,  # 24 hours in seconds
                    cleanup_old_jobs.s(days=30),
                    name='Cleanup old jobs daily'
                )
                
                print("📅 Periodic tasks scheduled for Celery")
                
            except Exception as e:
                print(f"⚠️  Failed to schedule periodic tasks: {str(e)}")
    except Exception as e:
        print(f"⚠️  Could not setup Celery periodic tasks: {e}")

# ============================================================================
# WEB TASK TRIGGER ENDPOINTS (For PythonAnywhere)
# ============================================================================

def get_task_routes():
    """Get web routes for triggering tasks on PythonAnywhere"""
    
    if IS_PYTHONANYWHERE:
        from flask import Blueprint, jsonify, request
        
        task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')
        
        @task_bp.route('/refresh-jobs', methods=['POST'])
        def trigger_refresh_jobs():
            """Trigger job refresh manually"""
            result = refresh_jobs()
            return jsonify(result)
        
        @task_bp.route('/fetch-new-jobs', methods=['POST'])
        def trigger_fetch_new_jobs():
            """Trigger new job fetch manually"""
            data = request.get_json() if request.is_json else {}
            keywords = data.get('keywords')
            max_per_keyword = data.get('max_per_keyword', 50)
            result = fetch_new_jobs(keywords, max_per_keyword)
            return jsonify(result)
        
        @task_bp.route('/cleanup-jobs', methods=['POST'])
        def trigger_cleanup_jobs():
            """Trigger job cleanup manually"""
            data = request.get_json() if request.is_json else {}
            days = data.get('days', 30)
            result = cleanup_old_jobs(days)
            return jsonify(result)
        
        @task_bp.route('/status')
        def task_status():
            """Get task execution status"""
            return jsonify({
                'environment': 'pythonanywhere',
                'celery_enabled': False,
                'tasks_available': ['refresh_jobs', 'fetch_new_jobs', 'cleanup_old_jobs'],
                'note': 'Tasks run synchronously on PythonAnywhere free tier'
            })
        
        return task_bp
    
    return None

# ============================================================================
# INITIALIZATION
# ============================================================================

print(f"✅ Tasks module initialized")
print(f"   • Environment: {'PythonAnywhere' if IS_PYTHONANYWHERE else 'Local/Production'}")
print(f"   • Celery: {'Disabled' if IS_PYTHONANYWHERE else 'Enabled'}")
print(f"   • Tasks available: refresh_jobs, fetch_new_jobs, cleanup_old_jobs")