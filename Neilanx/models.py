from datetime import datetime
from app import db
from sqlalchemy import func

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(20), default='free')  # free, premium
    monthly_reviews_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    onboarding_completed = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=True)
    
    # Relationship
    review_uploads = db.relationship('ReviewUpload', backref='user', lazy=True)

class ReviewUpload(db.Model):
    __tablename__ = 'review_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    total_reviews = db.Column(db.Integer, nullable=False)
    processed_reviews = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    reviews = db.relationship('Review', backref='upload', lazy=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('review_uploads.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 stars if available
    platform = db.Column(db.String(50))  # google, trustpilot, shopify, etc.
    reviewer_name = db.Column(db.String(100))
    review_date = db.Column(db.DateTime)
    
    # Sentiment analysis results
    sentiment = db.Column(db.String(20))  # positive, negative, neutral
    sentiment_score = db.Column(db.Float)  # confidence score 0-1
    keywords = db.Column(db.Text)  # JSON string of extracted keywords
    
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upload_id = db.Column(db.Integer, db.ForeignKey('review_uploads.id'), nullable=False)
    report_type = db.Column(db.String(20), default='summary')  # summary, detailed
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    upload = db.relationship('ReviewUpload', backref='reports', lazy=True)
