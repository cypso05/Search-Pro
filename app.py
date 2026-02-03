import os
import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()

# ============================================================================
# ENVIRONMENT DETECTION & CONFIGURATION
# ============================================================================

# Detect if running on PythonAnywhere
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ

def create_app(config_name=None):
    """Factory function to create Flask app with environment-aware config"""
    
    if config_name is None:
        # Auto-detect environment
        if IS_PYTHONANYWHERE:
            config_name = 'production'
            print("🚀 Running in production mode on PythonAnywhere")
        else:
            config_name = 'development'
            print("🔧 Running in development mode locally")
    
    app = Flask(__name__)
    
    # ============================================================================
    # CONFIGURATION BASED ON ENVIRONMENT
    # ============================================================================
    
    # API Configuration
    RAPID_API_KEY = os.getenv('RAPID_API_KEY')
    RAPID_API_HOST = os.getenv('RAPID_API_HOST', 'real-time-web-search.p.rapidapi.com')
    
    # Search Configuration
    MAX_RESULTS_PER_REQUEST = 100
    RESULTS_PER_PAGE = 15
    
    # Cache Configuration
    if IS_PYTHONANYWHERE:
        # PythonAnywhere: Use in-memory cache (Redis not available on free tier)
        CACHE_DURATION = 1800  # 30 minutes (shorter for memory)
        LAZY_LOAD_PAGES = 2    # Pre-load fewer pages on PythonAnywhere
        REDIS_AVAILABLE = False
        print("💾 Using in-memory cache (PythonAnywhere free tier)")
    else:
        # Local/Production: Use Redis
        CACHE_DURATION = 3600  # 1 hour cache
        LAZY_LOAD_PAGES = 3    # Pre-load next 3 pages
        
        # Try to connect to Redis
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD', None),
                decode_responses=True
            )
            redis_client.ping()
            REDIS_AVAILABLE = True
            print("✅ Redis cache connected")
        except:
            REDIS_AVAILABLE = False
            print("⚠️  Redis not available, using in-memory cache")
    
    # Store config in app
    app.config.update(
        # API
        RAPID_API_KEY=RAPID_API_KEY,
        RAPID_API_HOST=RAPID_API_HOST,
        
        # Search
        MAX_RESULTS_PER_REQUEST=MAX_RESULTS_PER_REQUEST,
        RESULTS_PER_PAGE=RESULTS_PER_PAGE,
        
        # Cache
        CACHE_DURATION=CACHE_DURATION,
        LAZY_LOAD_PAGES=LAZY_LOAD_PAGES,
        REDIS_AVAILABLE=REDIS_AVAILABLE,
        IS_PYTHONANYWHERE=IS_PYTHONANYWHERE,
        
        # Security
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        
        # Environment
        DEBUG=not IS_PYTHONANYWHERE,  # Debug only locally
    )
    
    # Initialize cache
    if REDIS_AVAILABLE:
        app.config['CACHE_TYPE'] = 'redis'
        app.config['redis_client'] = redis_client
    else:
        app.config['CACHE_TYPE'] = 'memory'
        app.config['memory_cache'] = {}
    
    # ============================================================================
    # CACHE FUNCTIONS (Environment Aware)
    # ============================================================================
    
    def get_cache_key(query, job_type='', search_type='general'):
        """Generate a unique cache key for search"""
        key_string = f"{search_type}:{query}:{job_type}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cache_set(key, data, duration=CACHE_DURATION):
        """Set cache with duration"""
        try:
            if REDIS_AVAILABLE:
                redis_client.setex(key, duration, json.dumps(data))
            else:
                memory_cache = app.config.get('memory_cache', {})
                memory_cache[key] = {
                    'data': data,
                    'expires': time.time() + duration
                }
                app.config['memory_cache'] = memory_cache
            return True
        except:
            return False
    
    def cache_get(key):
        """Get cached data"""
        try:
            if REDIS_AVAILABLE:
                cached = redis_client.get(key)
                return json.loads(cached) if cached else None
            else:
                memory_cache = app.config.get('memory_cache', {})
                if key in memory_cache:
                    cache_item = memory_cache[key]
                    if time.time() < cache_item['expires']:
                        return cache_item['data']
                    else:
                        del memory_cache[key]
                        app.config['memory_cache'] = memory_cache
                return None
        except:
            return None
    
    # Store cache functions in app context
    app.cache_set = cache_set
    app.cache_get = cache_get
    app.get_cache_key = get_cache_key
    
    # ============================================================================
    # ROUTES
    # ============================================================================
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/job-search')
    def job_search():
        return render_template('job_search.html')
    
    @app.route('/general-search')
    def general_search():
        return render_template('general_search.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'environment': 'pythonanywhere' if IS_PYTHONANYWHERE else 'local',
            'cache_enabled': True,
            'cache_type': 'redis' if REDIS_AVAILABLE else 'memory',
            'max_results_per_request': MAX_RESULTS_PER_REQUEST,
            'results_per_page': RESULTS_PER_PAGE,
            'cache_duration': CACHE_DURATION,
            'api_configured': bool(RAPID_API_KEY),
            'tasks_available': IS_PYTHONANYWHERE  # Tasks available on PythonAnywhere
        })
    
    @app.route('/api/environment')
    def environment_info():
        """Get environment information"""
        return jsonify({
            'is_pythonanywhere': IS_PYTHONANYWHERE,
            'cache_type': 'redis' if REDIS_AVAILABLE else 'memory',
            'debug_mode': app.config['DEBUG'],
            'available_features': {
                'redis': REDIS_AVAILABLE,
                'background_tasks': not IS_PYTHONANYWHERE,  # No Celery on PythonAnywhere free
                'email_sending': not IS_PYTHONANYWHERE,     # Limited on PythonAnywhere
                'file_uploads': True,
                'api_search': bool(RAPID_API_KEY),
                'manual_tasks': IS_PYTHONANYWHERE  # Manual task triggering on PythonAnywhere
            }
        })
    
    # ============================================================================
    # TASK ROUTES INTEGRATION (For PythonAnywhere)
    # ============================================================================
    
    # Import task routes with error handling
    try:
        # Only try to import if we're on PythonAnywhere
        if IS_PYTHONANYWHERE:
            from utils.tasks import get_task_routes
            
            task_bp = get_task_routes()
            if task_bp:
                app.register_blueprint(task_bp)
                print("✅ Task routes registered for PythonAnywhere")
    except ImportError as e:
        print(f"ℹ️  Task routes not available: {e}")
    except Exception as e:
        print(f"⚠️  Error with task routes: {e}")
    
    # ============================================================================
    # SEARCH FUNCTIONS
    # ============================================================================
    
    def make_search_request(query, limit=100):
        """Make API request with error handling"""
        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": RAPID_API_HOST
        }
        
        url = "https://real-time-web-search.p.rapidapi.com/search"
        params = {"q": query, "limit": str(limit)}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                app.logger.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            app.logger.error(f"Request Error: {str(e)}")
            return None
    
    def fetch_results_with_cache(query, job_type='', search_type='general', force_refresh=False):
        """Fetch results with caching and lazy loading support"""
        cache_key = get_cache_key(query, job_type, search_type)
        
        # Try to get from cache first (unless force refresh)
        if not force_refresh:
            cached_data = cache_get(cache_key)
            if cached_data:
                app.logger.info(f"Cache hit for: {query}")
                return cached_data['all_results'], cached_data['job_results']
        
        app.logger.info(f"Cache miss, fetching fresh results for: {query}")
        
        # Build search query based on type
        if search_type == 'jobs':
            search_query = f"{query} job"
            if job_type:
                search_query += f" {job_type}"
            search_query += " site:linkedin.com OR site:indeed.com OR site:glassdoor.com"
        else:
            search_query = query
        
        # Fetch initial results (fast)
        initial_data = make_search_request(search_query, limit=MAX_RESULTS_PER_REQUEST)
        all_results = initial_data.get('data', []) if initial_data else []
        
        # PythonAnywhere: Limit extra requests to avoid timeouts
        max_extra_requests = 2 if IS_PYTHONANYWHERE else 3
        
        # Start background lazy loading for more results
        if search_type == 'jobs' and len(all_results) > 0:
            extra_queries = [
                f"{query} {job_type} careers",
                f"{query} {job_type} hiring",
                f"{query} {job_type} employment"
            ]
            
            for i, extra_query in enumerate(extra_queries):
                if i >= max_extra_requests or len(all_results) >= 300:
                    break
                    
                extra_data = make_search_request(extra_query, limit=50)
                if extra_data:
                    # Merge and deduplicate
                    for result in extra_data.get('data', []):
                        url = result.get('url', '')
                        if url and not any(r.get('url') == url for r in all_results):
                            all_results.append(result)
                
                # Be nice to the API
                if not IS_PYTHONANYWHERE:
                    time.sleep(0.3)
        
        # Filter job results if needed
        job_results = []
        if search_type == 'jobs':
            for result in all_results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                url = result.get('url', '').lower()
                
                job_keywords = ['job', 'career', 'hire', 'hiring', 'employment']
                job_domains = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com']
                
                is_job_site = any(domain in url for domain in job_domains)
                has_job_keywords = any(keyword in title or keyword in snippet for keyword in job_keywords)
                
                if is_job_site or has_job_keywords:
                    cleaned_result = {
                        'title': result.get('title', ''),
                        'url': result.get('url', result.get('link', '')),
                        'snippet': result.get('snippet', result.get('description', '')),
                        'source': result.get('source', ''),
                        'domain': result.get('domain', ''),
                        'date': result.get('date', ''),
                        'type': 'job'
                    }
                    
                    # Apply job type filter
                    if job_type:
                        type_keywords = {
                            'remote': ['remote', 'work from home', 'wfh'],
                            'full-time': ['full-time', 'full time'],
                            'part-time': ['part-time', 'part time'],
                            'contract': ['contract', 'freelance'],
                            'internship': ['internship', 'intern']
                        }
                        
                        if job_type in type_keywords:
                            keywords = type_keywords[job_type]
                            title_lower = cleaned_result['title'].lower()
                            snippet_lower = cleaned_result['snippet'].lower()
                            if any(keyword in title_lower or keyword in snippet_lower for keyword in keywords):
                                job_results.append(cleaned_result)
                        else:
                            job_results.append(cleaned_result)
                    else:
                        job_results.append(cleaned_result)
        else:
            # General search - just clean results
            for result in all_results:
                cleaned_result = {
                    'title': result.get('title', ''),
                    'url': result.get('url', result.get('link', '')),
                    'snippet': result.get('snippet', result.get('description', '')),
                    'source': result.get('source', ''),
                    'domain': result.get('domain', ''),
                    'date': result.get('date', ''),
                    'type': 'general'
                }
                job_results.append(cleaned_result)
        
        # Cache the results
        cache_data = {
            'all_results': all_results,
            'job_results': job_results,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'job_type': job_type,
            'search_type': search_type
        }
        
        cache_set(cache_key, cache_data)
        
        return all_results, job_results
    
    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    
    @app.route('/api/search/jobs', methods=['POST'])
    def search_jobs():
        data = request.get_json()
        query = data.get('query', '').strip()
        page = int(data.get('page', 1))
        job_type = data.get('job_type', '')
        force_refresh = data.get('force_refresh', False)
        
        if not query:
            return jsonify({'error': 'Please enter a search query'}), 400
        
        try:
            # Fetch results (with cache)
            all_results, filtered_results = fetch_results_with_cache(
                query, job_type, 'jobs', force_refresh
            )
            
            # Pagination
            total_results = len(filtered_results)
            total_pages = max(1, (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
            
            # Get current page
            start_idx = (page - 1) * RESULTS_PER_PAGE
            end_idx = start_idx + RESULTS_PER_PAGE
            page_results = filtered_results[start_idx:end_idx]
            
            response = {
                'success': True,
                'query': query,
                'results': page_results,
                'total': total_results,
                'page': page,
                'total_pages': total_pages,
                'results_per_page': RESULTS_PER_PAGE,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'cached': not force_refresh,
                'total_fetched': len(all_results),
                'environment': 'pythonanywhere' if IS_PYTHONANYWHERE else 'local'
            }
            
            # PythonAnywhere: Skip background pre-fetching
            if not IS_PYTHONANYWHERE and page == 1 and total_pages > 1:
                # In production, this would be a background task
                app.logger.info(f"Background pre-fetching enabled for {query}")
            
            return jsonify(response)
            
        except Exception as e:
            app.logger.error(f"Search Error: {str(e)}")
            return jsonify({'error': 'Search failed. Please try again.'}), 500
    
    @app.route('/api/search/general', methods=['POST'])
    def search_general():
        data = request.get_json()
        query = data.get('query', '').strip()
        page = int(data.get('page', 1))
        force_refresh = data.get('force_refresh', False)
        
        if not query:
            return jsonify({'error': 'Please enter a search query'}), 400
        
        try:
            # Fetch results (with cache)
            all_results, filtered_results = fetch_results_with_cache(
                query, '', 'general', force_refresh
            )
            
            # Pagination
            total_results = len(filtered_results)
            total_pages = max(1, (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
            
            # Get current page
            start_idx = (page - 1) * RESULTS_PER_PAGE
            end_idx = start_idx + RESULTS_PER_PAGE
            page_results = filtered_results[start_idx:end_idx]
            
            response = {
                'success': True,
                'query': query,
                'results': page_results,
                'total': total_results,
                'page': page,
                'total_pages': total_pages,
                'results_per_page': RESULTS_PER_PAGE,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'cached': not force_refresh,
                'total_fetched': len(all_results),
                'environment': 'pythonanywhere' if IS_PYTHONANYWHERE else 'local'
            }
            
            return jsonify(response)
            
        except Exception as e:
            app.logger.error(f"Search Error: {str(e)}")
            return jsonify({'error': 'Search failed. Please try again.'}), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear all cache"""
        try:
            if REDIS_AVAILABLE:
                redis_client.flushdb()
            else:
                app.config['memory_cache'] = {}
            
            return jsonify({
                'success': True, 
                'message': 'Cache cleared',
                'cache_type': 'redis' if REDIS_AVAILABLE else 'memory'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/cache/stats')
    def cache_stats():
        """Get cache statistics"""
        try:
            if REDIS_AVAILABLE:
                keys = redis_client.keys('*')
                return jsonify({
                    'cache_type': 'redis',
                    'total_keys': len(keys),
                    'status': 'connected',
                    'environment': 'pythonanywhere' if IS_PYTHONANYWHERE else 'local'
                })
            else:
                memory_cache = app.config.get('memory_cache', {})
                return jsonify({
                    'cache_type': 'memory',
                    'total_items': len(memory_cache),
                    'status': 'active',
                    'environment': 'pythonanywhere' if IS_PYTHONANYWHERE else 'local'
                })
        except:
            return jsonify({'error': 'Cache not available'}), 500
    
    # ============================================================================
    # STARTUP MESSAGE
    # ============================================================================
    
    @app.before_request
    def before_first_request():
        if not hasattr(app, 'startup_message_printed'):
            app.startup_message_printed = True
            print("\n" + "="*60)
            print("🚀 DUAL MODE SEARCH ENGINE")
            print("="*60)
            print(f"✅ Environment: {'PythonAnywhere' if IS_PYTHONANYWHERE else 'Local Development'}")
            print(f"📊 Cache: {'Redis' if REDIS_AVAILABLE else 'In-memory'}")
            print(f"🔑 RapidAPI: {'Configured' if RAPID_API_KEY else 'NOT SET'}")
            print(f"⏱️  Cache duration: {CACHE_DURATION} seconds")
            print(f"📄 Results per page: {RESULTS_PER_PAGE}")
            print("="*60)
            print("🌐 Available endpoints:")
            print("   • Home: /")
            print("   • Job Search: /job-search")
            print("   • General Search: /general-search")
            print("   • Health Check: /health")
            print("   • Environment Info: /api/environment")
            print("   • Cache Stats: /api/cache/stats")
            if IS_PYTHONANYWHERE:
                print("   • Task Triggers: /api/tasks/*")
            print("="*60 + "\n")
    
    return app


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

# Create the app instance
app = create_app()

if __name__ == '__main__':
    # Only run development server locally, not on PythonAnywhere
    if not IS_PYTHONANYWHERE:
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("📝 Note: On PythonAnywhere, the app is served via WSGI, not __main__")
        print("💡 Use the PythonAnywhere Web tab to configure your WSGI file")