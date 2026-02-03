job-search-pro/
|-- Config.py
|-- Procfile
|-- README.md
|--venv
|-- .env  
|-- app.py
|-- docker-compose.yml
|-- dockerfile
|-- wsgi.py
|-- models
| |-- **pycache**
| | |-- job.cpython-312.pyc
| | |-- search.cpython-312.pyc
| | `-- user.cpython-312.pyc
|   |-- init.py
|   |-- job.py
|   |-- search.py
|   `-- user.py
|-- requirements.txt
|-- routes
| |--
| |-- api.py
| |-- auth.py
| `-- jobs.py
|-- runtime.txt
|-- setup_db.py
|-- templates
|   |-- general_search.html
|   |-- index.html
|   `-- job_search.html
|-- utils
| `-- tasks.py

# 🚀 Job Search Engine Pro

A full-featured, production-ready job search engine built with Flask, PostgreSQL, and modern web technologies. Search thousands of jobs, save favorites, track applications, and find your dream job faster.

## ✨ Features

- 🔍 **Advanced Job Search** - Search across multiple job boards with filters
- 👤 **User Authentication** - Secure login/registration with password hashing
- 💾 **Save Jobs** - Bookmark jobs and organize them by status
- 📊 **Application Tracking** - Track your job applications with status updates
- 📈 **Dashboard** - Personalized dashboard with search history and stats
- 🔄 **Real-time Updates** - Background job fetching with Celery
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🔒 **Production Ready** - Secure, scalable, and ready for deployment

## 🏗️ Project Structure

job-search-pro/
├── app.py # Main Flask application
├── config.py # Configuration settings
├── setup_db.py # Database initialization
├── requirements.txt # Python dependencies
├── .env # Environment variables (create from .env.example)
├── .gitignore # Git ignore file
├── Procfile # Heroku deployment config
├── runtime.txt # Python runtime version
├── wsgi.py # WSGI entry point
├── models/ # Database models
│ ├── init.py
│ ├── user.py
│ ├── job.py
│ ├── saved_job.py
│ └── search.py
├── routes/ # Application routes/blueprints
│ ├── init.py
│ ├── auth.py
│ ├── jobs.py
│ └── api.py
├── templates/ # HTML templates
│ ├── base.html
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── dashboard.html
│ └── search.html
├── static/ # Static assets
│ ├── css/
│ ├── js/
│ └── images/
└── utils/ # Utilities
├── init.py
├── database.py
└── helpers.py

text

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for caching)
- Git

### 1. Clone and Setup

````bash
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

# Edit .env with your settings
# Required: DATABASE_URL, SECRET_KEY, RAPID_API_KEY
Example .env file:

env
# Flask
SECRET_KEY=your-secret-key-change-this
FLASK_ENV=development
FLASK_APP=app.py

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/jobsearch

# API Keys
RAPID_API_KEY=your-rapidapi-key-here
RAPID_API_HOST=real-time-web-search.p.rapidapi.com

# Admin User
ADMIN_EMAIL=admin@jobsearch.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Optional: Redis for caching
# REDIS_URL=redis://localhost:6379/0
3. Setup PostgreSQL Database
bash
# Create PostgreSQL database (if not exists)
createdb jobsearch

# Or using psql:
# psql -U postgres
# CREATE DATABASE jobsearch;
# \q
4. Initialize Database
bash
# Run database setup
python setup_db.py
You should see:

text
✅ Database setup complete!
5. Run the Application
bash
# Development mode
python app.py

# Or with auto-reload
flask run --debug
The application will be available at: http://localhost:5000

📦 Database Setup Details
Manual Setup with setup_db.py
If you need to reset or recreate the database:

bash
# Drop and recreate (careful - deletes all data!)
psql -U postgres -c "DROP DATABASE IF EXISTS jobsearch;"
psql -U postgres -c "CREATE DATABASE jobsearch;"

# Run setup
python setup_db.py
Database Tables Created
users - User accounts and authentication

jobs - Job listings from various sources

saved_jobs - User-saved jobs with status tracking

job_applications - Job application tracking

search_history - User search queries and filters

🔧 Configuration
Environment Variables
Variable	Description	Default
DATABASE_URL	PostgreSQL connection URL	postgresql://user:password@localhost/jobsearch
SECRET_KEY	Flask secret key for sessions	(required)
RAPID_API_KEY	RapidAPI key for job search	(required)
RAPID_API_HOST	RapidAPI host	real-time-web-search.p.rapidapi.com
ADMIN_EMAIL	Default admin email	admin@jobsearch.com
ADMIN_USERNAME	Default admin username	admin
ADMIN_PASSWORD	Default admin password	admin123
REDIS_URL	Redis URL for caching	redis://localhost:6379/0
Application Configuration
Edit config.py for additional settings:

RESULTS_PER_PAGE: Number of results per page (default: 10)

MAX_RESULTS: Maximum results per search (default: 100)

BCRYPT_LOG_ROUNDS: Password hashing rounds (default: 12)

SESSION_TYPE: Session storage type (default: redis)

🌐 API Endpoints
Authentication
POST /api/v1/register - Register new user

POST /api/v1/login - User login

GET /api/v1/logout - User logout

GET /api/v1/profile - Get user profile

Job Search
GET /api/v1/search - Search jobs

GET /api/v1/jobs/<id> - Get job details

POST /api/v1/jobs/save - Save/unsave job

GET /api/v1/jobs/saved - Get saved jobs

User Dashboard
GET /api/v1/dashboard - User dashboard data

GET /api/v1/applications - User job applications

GET /api/v1/search-history - User search history

🎨 Frontend Templates
Available Pages
Home Page (/) - Landing page with search

Login (/login) - User login

Register (/register) - User registration

Dashboard (/dashboard) - User dashboard

Search Results (/search) - Job search results

Job Details (/jobs/<id>) - Individual job view

Saved Jobs (/saved-jobs) - User's saved jobs

Applications (/applications) - Job applications

Customizing Templates
Edit files in templates/ directory:

base.html - Base template with navigation

Custom CSS in static/css/

Custom JavaScript in static/js/

🔄 Background Tasks (Optional)
For automatic job updates and notifications:

bash
# Install Redis (if not installed)
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server

# In a new terminal, start Celery worker
celery -A utils.tasks.celery worker --loglevel=info

# Start Celery beat for scheduled tasks
celery -A utils.tasks.celery beat --loglevel=info
🚢 Deployment
Heroku Deployment
bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set RAPID_API_KEY=your-key
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run python setup_db.py

# Open app
heroku open
Docker Deployment
bash
# Build Docker image
docker build -t jobsearch-pro .

# Run with Docker Compose
docker-compose up -d
Docker Compose example (docker-compose.yml):

yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/jobsearch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: jobsearch
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

  celery:
    build: .
    command: celery -A utils.tasks.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/jobsearch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
🧪 Testing
bash
# Run tests
python -m pytest tests/

# Run with coverage
coverage run -m pytest
coverage report
🔍 Troubleshooting
Common Issues
Database Connection Error

bash
# Check PostgreSQL is running
psql -U postgres -c "\l"

# Check DATABASE_URL in .env
echo $DATABASE_URL
Module Import Errors

bash
# Make sure you're in the right directory
pwd

# Check Python path
python -c "import sys; print(sys.path)"
Port Already in Use

bash
# Find and kill process on port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:5000 | xargs kill -9
Missing Dependencies

bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
Getting API Keys
RapidAPI Key:

Visit https://rapidapi.com/contextualwebsearch/api/web-search

Sign up and subscribe to get your API key

Alternative APIs (optional):

SerpAPI: https://serpapi.com/

Indeed API: https://www.indeed.com/publisher

LinkedIn API: https://developer.linkedin.com/

📚 API Documentation
Once running, visit:

Swagger UI: http://localhost:5000/api/docs

ReDoc: http://localhost:5000/api/redoc

🔒 Security Best Practices
Always change default passwords

Use environment variables for secrets

Enable HTTPS in production

Regularly update dependencies

Implement rate limiting

Use CSRF protection

Validate all user inputs

Regular database backups

📈 Monitoring
Logs
bash
# View application logs
tail -f logs/jobsearch.log

# View database logs (PostgreSQL)
# Check your PostgreSQL log location
Health Check
bash
# Application health
curl http://localhost:5000/health

# Database health
psql $DATABASE_URL -c "SELECT now();"
🤝 Contributing
Fork the repository

Create a feature branch

Make your changes

Add tests

Submit a pull request

📄 License
MIT License - see LICENSE file for details

🙏 Acknowledgments
Flask and Flask extensions community

PostgreSQL team

RapidAPI for search API

All open-source contributors

📞 Support
For issues and questions:

Check the Troubleshooting section

Search existing issues

Create a new issue with details

Happy Job Hunting! 🎯

Built with ❤️ by [Your Name]

text

## Quick Start Cheat Sheet

Also create a `QUICKSTART.md` for the absolute essentials:

```markdown
# ⚡ Quick Start Guide

## 5-Minute Setup

```bash
# 1. Clone and enter
git clone <repo>
cd job-search-pro

# 2. Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key

# 3. Create database
createdb jobsearch

# 4. Initialize
python setup_db.py

# 5. Run!
python app.py
Default Admin Login
Email: admin@jobsearch.com

Password: admin123

URLs
App: http://localhost:5000

API: http://localhost:5000/api/v1/search

Admin: http://localhost:5000/dashboard

Common Commands
bash
# Reset database
python setup_db.py

# Run tests
pytest

# Check logs
tail -f logs/jobsearch.log

# Update dependencies
pip freeze > requirements.txt
text

## Save These Files

1. Save the first code block as `README.md`
2. Save the second code block as `QUICKSTART.md`
3. Create a `.env.example` file:

```env
# Flask
SECRET_KEY=your-secret-key-change-this
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/jobsearch

# API Keys
RAPID_API_KEY=your-key-here
RAPID_API_HOST=real-time-web-search.p.rapidapi.com

# Admin
ADMIN_EMAIL=admin@jobsearch.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Optional
REDIS_URL=redis://localhost:6379/0
Next Steps After Setup
Now that your database is set up, here's what to do next:

bash
# 1. Start the application
python app.py

# 2. Open your browser to:
# http://localhost:5000

# 3. Login with:
# Email: admin@jobsearch.com
# Password: admin123

# 4. Start searching for jobs!
Your job search engine is now ready to use! The admin user is created, database tables are set up, and you can start searching for jobs immediately.
````
