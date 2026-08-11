import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func

# PostgreSQL Connection URI
POSTGRES_URI = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:66620915@localhost:5432/course_db'
)

engine = create_engine(POSTGRES_URI, echo=False)
metadata = MetaData()

# 1. Users Table
users = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False),
    Column('email', String(100), unique=True, nullable=False)
)

# 2. Courses Table (With RAG Metadata)
courses = Table(
    'courses', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(150), nullable=False),
    Column('category', String(100), nullable=False),
    Column('description', Text, nullable=False),
    Column('skills', Text, nullable=False),
    Column('prerequisites', Text, nullable=True),
    Column('topics', Text, nullable=True),
    Column('difficulty', String(50), default='Intermediate')
)

# 3. Skills Catalog Table
skills = Table(
    'skills', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, nullable=False)
)

# 4. User Skills Mapping Table
user_skills = Table(
    'user_skills', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('skill_name', String(100), nullable=False)
)

# 5. Recommendation Execution Logs
recommendation_logs = Table(
    'recommendation_logs', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, nullable=True),
    Column('query_text', String(255), nullable=True),
    Column('recommended_courses', Text, nullable=False),
    Column('timestamp', DateTime, default=func.now())
)

# --- LEVEL 3 NEW TABLES ---

# 6. Async Background Jobs Table
jobs = Table(
    'jobs', metadata,
    Column('job_id', String(100), primary_key=True),
    Column('status', String(50), nullable=False, default='pending'),  # pending, processing, completed, failed
    Column('result', Text, nullable=True),
    Column('created_at', DateTime, default=func.now()),
    Column('completed_at', DateTime, nullable=True)
)

# 7. Recommendation Feedback Loop Table
user_feedback = Table(
    'user_feedback', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=True),
    Column('course_id', Integer, ForeignKey('courses.id'), nullable=False),
    Column('action', String(50), nullable=False), # 'relevant', 'not_relevant', 'saved', 'enrolled'
    Column('timestamp', DateTime, default=func.now())
)