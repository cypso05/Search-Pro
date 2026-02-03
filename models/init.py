# models/__init__.py
from .user import User
from .job import Job, SavedJob, JobApplication
from .search import SearchHistory

__all__ = ['User', 'Job', 'SavedJob', 'JobApplication', 'SearchHistory']