# models/search.py
from datetime import datetime
from app import db

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    query = db.Column(db.String(500), nullable=False)
    filters = db.Column(db.JSON)  # Store filters as JSON
    result_count = db.Column(db.Integer, default=0)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', back_populates='search_history')
    
    # Indexes
    __table_args__ = (
        db.Index('ix_search_history_user_created', 'user_id', 'created_at'),
        db.Index('ix_search_history_query', 'query'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query': self.query,
            'filters': self.filters,
            'result_count': self.result_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }