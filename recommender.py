import uuid
import json
import threading
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.sql import select, insert, update, func
import db

# Load HuggingFace Transformer Model for Vector Embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')


# 1. TOOL AGENT FUNCTIONS

def get_user_skills_tool(user_id):
    """Tool: Retrieves stored user skills from PostgreSQL."""
    try:
        with db.engine.connect() as conn:
            stmt = select(db.user_skills.c.skill_name).where(db.user_skills.c.user_id == user_id)
            result = conn.execute(stmt).fetchall()
            return [row[0] for row in result]
    except Exception:
        return []


def search_courses_tool():
    """Tool: Fetches all courses with complete metadata from database."""
    try:
        with db.engine.connect() as conn:
            stmt = select(db.courses)
            result = conn.execute(stmt).fetchall()
            return [dict(row._mapping) for row in result]
    except Exception:
        return []


def analyze_skill_gap_tool(user_skills_list, course_skills_str):
    """Tool: Identifies matched skills and missing skill gaps."""
    if not course_skills_str:
        return [], []
    course_skills = [s.strip() for s in course_skills_str.split(',') if s.strip()]
    user_skills_set = set(s.lower() for s in user_skills_list)
    
    missing_skills = [s for s in course_skills if s.lower() not in user_skills_set]
    matched_skills = [s for s in course_skills if s.lower() in user_skills_set]
    
    return matched_skills, missing_skills


def generate_learning_path_tool(recommended_courses):
    """Tool: Multi-Agent Learning Path Planner (Sequences courses by difficulty)."""
    difficulty_rank = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
    sorted_courses = sorted(
        recommended_courses, 
        key=lambda x: difficulty_rank.get(x.get('difficulty', 'Intermediate'), 2)
    )
    
    learning_path = []
    for idx, course in enumerate(sorted_courses, start=1):
        learning_path.append({
            "step": idx,
            "title": course['title'],
            "difficulty": course.get('difficulty', 'Intermediate'),
            "prerequisites": course.get('prerequisites', 'None'),
            "key_skills": course.get('skills', '')
        })
    return learning_path


def get_user_feedback_score_adjustment(course_id):
    """Tool: Calculates score boost/penalty based on Recommendation Feedback Loop."""
    try:
        with db.engine.connect() as conn:
            stmt = select(db.user_feedback.c.action).where(db.user_feedback.c.course_id == course_id)
            feedback_list = conn.execute(stmt).fetchall()
            
        score_modifier = 0.0
        for fb in feedback_list:
            action = str(fb[0]).lower()
            if action == 'relevant':
                score_modifier += 5.0
            elif action == 'enrolled':
                score_modifier += 10.0
            elif action == 'saved':
                score_modifier += 3.0
            elif action == 'not_relevant':
                score_modifier -= 10.0
        return score_modifier
    except Exception:
        return 0.0


# 2. RAG-BASED COURSE KNOWLEDGE ASSISTANT


def rag_course_assistant(course_id, question):
    """RAG Assistant: Answers questions about syllabus and prerequisites."""
    all_courses = search_courses_tool()
    target = next((c for c in all_courses if c['id'] == course_id), None)
    
    if not target:
        return {"error": "Course profile not found in knowledge base."}
    
    context = (
        f"Course: {target['title']} | Category: {target['category']}\n"
        f"Difficulty: {target.get('difficulty', 'Intermediate')}\n"
        f"Topics: {target.get('topics', 'Core concepts')}\n"
        f"Prerequisites: {target.get('prerequisites', 'None')}\n"
        f"Description: {target['description']}"
    )
    
    q_lower = question.lower()
    if "prerequisite" in q_lower or "requirement" in q_lower:
        ans = f"To excel in '{target['title']}', prerequisites needed: {target.get('prerequisites', 'None')}."
    elif "learn" in q_lower or "topic" in q_lower:
        ans = f"In '{target['title']}', topics covered include: {target.get('topics', target['description'])}."
    else:
        ans = f"'{target['title']}' ({target.get('difficulty')}) description: {target['description']}"

    return {
        "course_id": course_id,
        "course_title": target['title'],
        "question": question,
        "retrieved_context": context,
        "answer": ans
    }


# 3. AGENTIC ORCHESTRATOR WORKFLOW


def run_agentic_workflow(user_id=None, query_text=None):
    """Executes Multi-Agent Recommendation Workflow."""
    extracted_skills = []
    if user_id is not None and str(user_id).isdigit():
        extracted_skills = get_user_skills_tool(int(user_id))
    elif query_text and str(query_text).strip():
        extracted_skills = [s.strip() for s in str(query_text).split(',') if s.strip()]
        
    if not extracted_skills:
        extracted_skills = ["Python", "General Technology"]

    courses_data = search_courses_tool()
    if not courses_data:
        return {"error": "No course data available"}

    corpus = [f"{c['title']} {c['category']} {c.get('skills', '')} {c['description']}" for c in courses_data]
    course_embeddings = model.encode(corpus, convert_to_numpy=True)
    
    user_query_str = ", ".join(extracted_skills)
    user_vector = model.encode([user_query_str], convert_to_numpy=True)

    similarities = cosine_similarity(user_vector, course_embeddings)[0]
    
    ranked_results = []
    for idx, raw_score in enumerate(similarities):
        course = courses_data[idx].copy()
        base_pct = float(raw_score) * 100
        
        feedback_mod = get_user_feedback_score_adjustment(course['id'])
        final_score = round(max(0.0, min(100.0, base_pct + feedback_mod)), 1)
        
        matched_skills, missing_skills = analyze_skill_gap_tool(extracted_skills, course.get('skills', ''))
        
        course['score_percentage'] = final_score
        course['matched_skills'] = matched_skills
        course['missing_skills'] = missing_skills
        course['explanation'] = (
            f"Matched {len(matched_skills)} skill(s) [{', '.join(matched_skills) if matched_skills else 'None'}]. "
            f"Missing skill gap: [{', '.join(missing_skills) if missing_skills else 'None'}]."
        )
        ranked_results.append(course)

    ranked_results = sorted(ranked_results, key=lambda x: x['score_percentage'], reverse=True)[:3]
    learning_path = generate_learning_path_tool(ranked_results)

    return {
        "user_id": user_id,
        "extracted_skills": extracted_skills,
        "recommended_courses": ranked_results,
        "learning_path": learning_path,
        "status": "success"
    }


# 4. ASYNC BACKGROUND WORKER THREAD


def process_async_job(job_id, user_id, query_text):
    """Execution-safe background thread worker."""
    time.sleep(0.5)
    try:
        result_payload = run_agentic_workflow(user_id=user_id, query_text=query_text)
        result_json_str = json.dumps(result_payload)

        with db.engine.begin() as conn:
            stmt = update(db.jobs).where(db.jobs.c.job_id == job_id).values(
                status='completed',
                result=result_json_str
            )
            conn.execute(stmt)
            
    except Exception as e:
        print(f"Async Job Execution Error: {e}")
        try:
            with db.engine.begin() as conn:
                stmt = update(db.jobs).where(db.jobs.c.job_id == job_id).values(
                    status='failed',
                    result=json.dumps({"error": str(e)})
                )
                conn.execute(stmt)
        except Exception:
            pass


def dispatch_async_job(user_id=None, query_text=None):
    """Enqueues async job and launches background thread."""
    job_id = str(uuid.uuid4())
    with db.engine.begin() as conn:
        stmt = insert(db.jobs).values(
            job_id=job_id,
            status='processing',
            result=None
        )
        conn.execute(stmt)

    worker_thread = threading.Thread(target=process_async_job, args=(job_id, user_id, query_text))
    worker_thread.start()
    return job_id