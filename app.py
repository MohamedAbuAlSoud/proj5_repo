import json
from flask import Flask, render_template, request, jsonify
from sqlalchemy.sql import select, insert
import db
from agentic_recommender import (
    dispatch_async_job, 
    run_agentic_workflow, 
    rag_course_assistant
)

app = Flask(__name__)

# Ensure all PostgreSQL tables exist
db.metadata.create_all(db.engine)


def get_all_users_list():
    """Helper: Fetches user list for frontend UI dropdowns."""
    try:
        with db.engine.connect() as conn:
            stmt = select(db.users)
            result = conn.execute(stmt).fetchall()
            return [dict(row._mapping) for row in result]
    except Exception:
        return []


def get_all_skills_list():
    """Helper: Extracts catalog skills for frontend UI filtering."""
    try:
        with db.engine.connect() as conn:
            stmt = select(db.courses)
            all_courses = conn.execute(stmt).fetchall()
            
        skills_set = set()
        for c in all_courses:
            skills_str = c._mapping['skills']
            for s in skills_str.split(','):
                skills_set.add(s.strip())
        return sorted(list(skills_set))
    except Exception:
        return []


# FRONTEND UI ROUTES

@app.route('/')
@app.route('/recommendation')
def recommendation():
    """Web interface for course recommendations."""
    user_query = request.args.get('query', '').strip()
    selected_user_id = request.args.get('user_id', '').strip()
    
    workflow_result = None
    if selected_user_id:
        workflow_result = run_agentic_workflow(user_id=int(selected_user_id))
    elif user_query:
        workflow_result = run_agentic_workflow(query_text=user_query)
    
    return render_template(
        'recommendation.html', 
        user_query=user_query, 
        selected_user_id=selected_user_id,
        users=get_all_users_list(),
        skills=get_all_skills_list(),
        results=workflow_result
    )


@app.route('/skills')
def skills():
    """Web interface listing system skills."""
    return render_template('skills.html', skills=get_all_skills_list())


@app.route('/courses')
def courses():
    """Web interface displaying full course catalog."""
    with db.engine.connect() as conn:
        stmt = select(db.courses)
        all_courses = conn.execute(stmt).fetchall()
        course_list = [dict(row._mapping) for row in all_courses]
    return render_template('courses.html', courses=course_list)


# BONUS LEVEL 3 REST API ENDPOINTS

# 1. POST /api/recommend -> Enqueue Async Job
@app.route('/api/recommend', methods=['POST'])
def api_recommend_async():
    """Dispatches asynchronous recommendation job to background queue thread."""
    data = request.get_json() if request.is_json else {}
    user_id = data.get('user_id')
    query_text = data.get('query')

    job_id = dispatch_async_job(user_id=user_id, query_text=query_text)

    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "poll_url": f"/api/recommend/{job_id}"
    }), 202


# 2. GET /api/recommend/<job_id> -> Poll Job Status & Get Output
@app.route('/api/recommend/<job_id>', methods=['GET'])
def get_recommend_job_status(job_id):
    """Polls job status and returns completed recommendation payload."""
    # Strip any accidental quotation marks or whitespace from URL string
    clean_job_id = job_id.strip('"').strip("'").strip()

    with db.engine.connect() as conn:
        stmt = select(db.jobs).where(db.jobs.c.job_id == clean_job_id)
        job = conn.execute(stmt).fetchone()

    if not job:
        return jsonify({"error": f"Job ID '{clean_job_id}' not found"}), 404

    job_mapping = job._mapping
    if job_mapping['status'] == 'completed':
        return jsonify({
            "job_id": clean_job_id,
            "status": "completed",
            "data": json.loads(job_mapping['result'])
        }), 200
    else:
        return jsonify({
            "job_id": clean_job_id,
            "status": job_mapping['status'],
            "data": json.loads(job_mapping['result']) if job_mapping['result'] else None
        }), 200


# 3. POST /api/feedback -> Recommendation Feedback Loop
@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """Stores user feedback interaction to adjust recommendation scoring."""
    data = request.get_json() if request.is_json else {}
    user_id = data.get('user_id')
    course_id = data.get('course_id')
    action = data.get('action')  # 'relevant', 'not_relevant', 'saved', 'enrolled'

    if not course_id or not action:
        return jsonify({"error": "course_id and action are required parameters"}), 400

    with db.engine.connect() as conn:
        stmt = insert(db.user_feedback).values(
            user_id=user_id,
            course_id=course_id,
            action=action
        )
        conn.execute(stmt)
        conn.commit()

    return jsonify({"status": "success", "message": "Feedback successfully recorded."}), 200


# 4. GET /api/rag/qa -> RAG Course Knowledge Assistant
@app.route('/api/rag/qa', methods=['GET'])
def api_rag_qa():
    """RAG-based Course Assistant answering questions on prerequisites and topics."""
    course_id = request.args.get('course_id', type=int)
    question = request.args.get('question', 'What will I learn?')

    if not course_id:
        return jsonify({"error": "course_id query parameter is required"}), 400

    response_data = rag_course_assistant(course_id, question)
    return jsonify(response_data), 200


if __name__ == '__main__':
    app.run(debug=True)