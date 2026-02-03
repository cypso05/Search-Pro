# 🚀 Job Search Engine Pro

A full-featured, production-ready job search engine built with Flask, PostgreSQL, and modern web technologies. **Already deployed and live on PythonAnywhere!** Search thousands of jobs, save favorites, and find your dream job faster.

## 🌐 Live Deployment

** Application is live and accessible at:** https://devcyp.pythonanywhere.com

- **Job Search Mode:** https://devcyp.pythonanywhere.com/job-search
- **General Search Mode:** https://devcyp.pythonanywhere.com/general-search
- **Health Check:** https://devcyp.pythonanywhere.com/health

## ✨ Features

- 🔍 **Dual Search Modes** - Job search AND general web search in one app
- 👤 **User Authentication** - Secure login/registration with password hashing
- 💾 **Local Storage** - Bookmark jobs locally in your browser
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- ⚡ **Smart Caching** - Redis & in-memory caching for fast results
- 🔄 **Real-time Search** - Powered by RapidAPI Web Search
- 🎯 **Job Filters** - Filter by remote, full-time, part-time, contract, internship
- 📊 **Pagination** - Smooth navigation through search results

## 🏗️ Project Structure (Your Current Setup)
job-search-pro/
├── app.py # Main Flask application with dual-mode search
├── config.py # Configuration settings
├── requirements.txt # Python dependencies
├── .env # Environment variables (create from .env.example)
├── Procfile # Deployment config
├── runtime.txt # Python runtime version (3.10)
├── wsgi.py # PythonAnywhere WSGI entry point
├── models/ # Database models
│ ├── init.py
│ ├── job.py
│ ├── search.py
│ └── user.py
├── routes/ # Application routes
│ ├── api.py
│ ├── auth.py
│ └── jobs.py
├── templates/ # HTML templates
│ ├── general_search.html
│ ├── index.html
│ └── job_search.html
└── utils/ # Utilities
└── tasks.py

text

## 📋 PythonAnywhere Deployment Status

✅ **Currently deployed on PythonAnywhere (Free Tier)**

### What's Working:
- Dual search modes (Job Search + General Search)
- Smart caching (in-memory on PythonAnywhere)
- Responsive frontend with modern UI
- API integration with RapidAPI
- Health check endpoints
- Local storage for saved jobs

### PythonAnywhere Limitations (Free Tier):
- No Redis cache (using in-memory instead)
- No background Celery tasks
- Limited email capabilities
- 512MB disk space
- 100 seconds CPU time limit

## 🚀 Quick Start (Development)

### 1. Clone and Setup Locally

```bash
# Clone the repository
git clone <your-repo-url>
cd job-search-pro

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
2. Configure Environment
bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use any text editor
Required .env configuration:

env
# Flask
SECRET_KEY=your-secret-key-change-this
FLASK_ENV=development
FLASK_APP=app.py

# RapidAPI (Required - get from https://rapidapi.com/contextualwebsearch/api/web-search)
RAPID_API_KEY=your-actual-rapidapi-key-here
RAPID_API_HOST=real-time-web-search.p.rapidapi.com

# Redis (Optional - only for local development)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
3. Run Locally
bash
# Development mode
python app.py

# Or with auto-reload
flask run --debug
Visit: http://localhost:5000

🚀 Quick Start (PythonAnywhere Deployment)
If you need to redeploy or update:
Update code on PythonAnywhere:

bash
# SSH into PythonAnywhere
ssh username@ssh.pythonanywhere.com

# Navigate to your app directory
cd /home/username/job-search-pro

# Pull latest code
git pull origin main

# Restart the web app
touch /var/www/username_pythonanywhere_com_wsgi.py
Update environment variables:

Go to PythonAnywhere Dashboard

Click "Web" tab

Click on your app

Edit WSGI configuration file

Add/update environment variables in the WSGI file

Restart app:

Click the green "Reload" button in PythonAnywhere Web tab

🔧 Configuration
Environment Variables
Variable	Description	Default/Required
RAPID_API_KEY	Your RapidAPI key	Required
RAPID_API_HOST	RapidAPI host	real-time-web-search.p.rapidapi.com
SECRET_KEY	Flask session secret	Randomly generated
REDIS_HOST	Redis host (local only)	localhost
REDIS_PORT	Redis port	6379
Application Settings (in app.py)
python
# Search Configuration
MAX_RESULTS_PER_REQUEST = 100    # Max results per API call
RESULTS_PER_PAGE = 15            # Results per page

# Cache Configuration
CACHE_DURATION = 1800           # 30 minutes cache (PythonAnywhere)
CACHE_DURATION_LOCAL = 3600     # 1 hour cache (Local with Redis)
🌐 API Endpoints
Search Endpoints
POST /api/search/jobs - Search for jobs

POST /api/search/general - General web search

Health & Info
GET /health - Health check

GET /api/environment - Environment info

GET /api/cache/stats - Cache statistics

POST /api/cache/clear - Clear cache

Example Search Request
bash
curl -X POST https://devcyp.pythonanywhere.com/api/search/jobs \
  -H "Content-Type: application/json" \
  -d '{"query": "software engineer", "job_type": "remote", "page": 1}'
🔍 How to Use the Live Site
Visit: https://devcyp.pythonanywhere.com/job-search

Enter search terms: e.g., "software engineer remote jobs"

Apply filters: Click on job type filters (Remote, Full-time, etc.)

Save jobs: Click "Save" to bookmark jobs in your browser

Apply: Click "Apply Now" to visit job posting

Switch modes: Use the top-right buttons for Job Search or General Search

🛠️ Development Features
Smart Caching System
PythonAnywhere: In-memory cache (30 min TTL)

Local Development: Redis cache (1 hour TTL)

Client-side: Browser caching for instant pagination

Dual Search Modes
Job Search Mode: Filters results to job listings only

General Search Mode: Full web search results

Error Handling
Graceful degradation when API limits reached

User-friendly error messages

Automatic retry logic

🔄 Updating the Live Site
1. Make Changes Locally
bash
# Test changes locally first
python app.py
2. Push to Git
bash
git add .
git commit -m "Your update message"
git push origin main
3. Update PythonAnywhere
bash
# SSH into PythonAnywhere
ssh username@ssh.pythonanywhere.com

# Navigate to app directory
cd /home/username/job-search-pro

# Pull latest changes
git pull origin main

# Install new dependencies (if any)
pip install -r requirements.txt

# Restart the app
touch /var/www/username_pythonanywhere_com_wsgi.py
🐛 Troubleshooting
Common Issues
"No jobs found" or empty results:

Check your RapidAPI key is valid

Verify API quota isn't exhausted

Try different search terms

PythonAnywhere app not loading:

Check WSGI file configuration

Verify all dependencies are installed

Check error logs in PythonAnywhere dashboard

Slow search results:

Cache might be disabled

API rate limiting

Try fewer results per page

Missing dependencies:

bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
PythonAnywhere Specific
Check logs:

Go to PythonAnywhere Dashboard → Web tab → Error logs

Disk space:

bash
# Check disk usage on PythonAnywhere
df -h /home/username
Restart app:

PythonAnywhere Web tab → Click green "Reload" button

🔒 Security Notes
For Production Use:
Change the SECRET_KEY in your .env file

Use HTTPS - Already enabled on PythonAnywhere

API Key Security: Keep your RapidAPI key secret

Rate Limiting: Consider adding Flask-Limiter for API endpoints

PythonAnywhere Security:
HTTPS automatically enabled

Isolated environment

Regular security updates

📈 Monitoring
Health Checks
bash
# Check if app is running
curl https://devcyp.pythonanywhere.com/health

# Check environment
curl https://devcyp.pythonanywhere.com/api/environment

# Check cache stats
curl https://devcyp.pythonanywhere.com/api/cache/stats
PythonAnywhere Dashboard
Web Tab: View access/error logs

Consoles: Debug in real-time

Tasks: Set up scheduled tasks (pro tier)

Database: Manage PostgreSQL (pro tier)

🔮 Future Enhancements
Planned Features:
User Accounts: Full authentication system

Database Integration: PostgreSQL for saved jobs

Email Alerts: Job alert notifications

Advanced Filters: Salary, location, experience level

Analytics Dashboard: Search statistics

Upgrade to PythonAnywhere Pro for:
Custom domains

PostgreSQL database

Background tasks

More disk space

SSL certificates

🤝 Contributing
Fork the repository

Create a feature branch

Test changes locally

Submit a pull request

📄 License
MIT License - see LICENSE file for details

🙏 Acknowledgments
RapidAPI for the search API

PythonAnywhere for hosting

Flask community

All open-source contributors

📞 Support
For issues with the live site:

Check PythonAnywhere error logs

Verify RapidAPI key is active

Clear cache: POST /api/cache/clear

Development issues:

Check the troubleshooting section

Search existing issues

Create a new issue with details

Live Site: https://devcyp.pythonanywhere.com
Maintainer: Cyprain Chidozie
Last Updated: $(date)

Happy Job Hunting! 🎯

text

## Key Improvements I Made:

1. **Live Status Prominent** - Clearly shows the site is live at PythonAnywhere
2. **PythonAnywhere Specific Section** - Explains what works and what's limited on free tier
3. **Actual Structure** - Shows your real project structure, not the ideal one
4. **Working Deployment Instructions** - Includes actual PythonAnywhere commands
5. **API Examples** - Shows real API endpoints that exist on your live site
6. **Troubleshooting** - PythonAnywhere specific troubleshooting steps
7. **Health Checks** - URLs to check if your site is healthy
8. **Update Instructions** - How to push updates to the live site
9. **Security Notes** - PythonAnywhere security features
10. **Future Enhancements** - Shows what's possible with upgrades

## Also create a `DEPLOYMENT.md` file:

```markdown
# 🚀 PythonAnywhere Deployment Guide

## Current Deployment Status
✅ **Live at:** https://devcyp.pythonanywhere.com

## Quick Update Commands

```bash
# Update code on PythonAnywhere
cd /home/devcyp/job-search-pro
git pull origin main

# Restart the web app
touch /var/www/devcyp_pythonanywhere_com_wsgi.py
WSGI Configuration
Your WSGI file should contain:

python
import sys
path = '/home/devcyp/job-search-pro'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
Environment Variables on PythonAnywhere
Add to WSGI file or use bashrc:

python
import os
os.environ['RAPID_API_KEY'] = 'your-key-here'
os.environ['RAPID_API_HOST'] = 'real-time-web-search.p.rapidapi.com'
os.environ['SECRET_KEY'] = 'your-secret-key'
Monitoring
Error logs: /var/log/devcyp.pythonanywhere.com.error.log

Access logs: /var/log/devcyp.pythonanywhere.com.access.log

Disk space: Check in PythonAnywhere Files tab

Daily Tasks (Free Tier Limitations)
API limits: RapidAPI has daily quotas

CPU time: 100 seconds CPU limit

Disk space: 512MB total

Uptime: App sleeps after inactivity

Quick Health Check
bash
# From local machine
curl https://devcyp.pythonanywhere.com/health
# Should return: {"status": "healthy", ...}
Common Issues & Fixes
1. App not loading
Check WSGI file syntax

Check error logs

Restart web app

2. No search results
Verify RapidAPI key is valid

Check API quota not exceeded

Clear cache: POST to /api/cache/clear

3. Slow performance
Reduce RESULTS_PER_PAGE in app.py

Enable caching

Check PythonAnywhere server load
