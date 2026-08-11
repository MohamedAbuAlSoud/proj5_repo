# proj5_repo
 # 🤖 Level 3: Agentic Course Recommendation & Asynchronous Pipeline

An intelligent, multi-agent AI system built with **Flask**, **PostgreSQL**, **SQLAlchemy Core**, **SentenceTransformers**, and **Bootstrap 5**. The application delivers personalized course recommendations using semantic vector search, dynamic feedback scoring, skill-gap analysis, asynchronous job processing, and a RAG knowledge assistant.

---

## 🌟 Key Features (Bonus Level 3)

* **🤖 Agentic Recommendation Workflow**:
  * **Profile & Skill Extractor Agent**: Parses target user profiles or free-form natural language queries into structured skill competencies.
  * **Semantic Matcher**: Computes cosine similarity across course corpus embeddings using HuggingFace's `all-MiniLM-L6-v2` transformer model.
  * **Skill Gap Analyzer Agent**: Compares user capabilities against target course syllabi to highlight matched skills vs. missing skill gaps.
  * **Multi-Agent Learning Path Planner**: Sequences recommended courses logically by difficulty levels (Beginner → Intermediate → Advanced).

* **⚡ Asynchronous Background Job Processing (`POST` & `GET` Polling)**:
  * Offloads heavy transformer inference and multi-agent execution to background threads using a persistent job queue stored in PostgreSQL (`jobs` table).
  * Returns an instant HTTP `202 Accepted` response with a unique `job_id` and a polling URL.

* **🔁 Recommendation Feedback Loop**:
  * Dynamic score adjustments based on historical user interactions (`relevant`, `saved`, `enrolled`, `not_relevant`).

* **📚 RAG-Based Course Knowledge Assistant**:
  * Retrieval-Augmented Generation endpoint answering detailed questions about prerequisites, syllabi, and course topics.

---

## 🏗️ System Architecture

+------------------------+
                            |  Flask Web / REST API   |
                            +-----------+------------+
                                        |
     +----------------------------------+----------------------------------+
     |                                  |                                  |
     v                                  v                                  v

+------------------+              +------------------+              +------------------+
| Async Job Queue  |              | Feedback Loop    |              | RAG Assistant    |
| (Background)     |              | (Score Modifier) |              | Knowledge Base   |
+--------+---------+              +--------+---------+              +--------+---------+
|                                  |                                  |
+----------------------------------+----------------------------------+
|
v
+------------------------+
|  PostgreSQL Database   |
+------------------------+


---

## 🚀 API Documentation & Endpoints

### 1. Enqueue Async Recommendation Job
* **URL**: `/api/recommend`
* **Method**: `POST`
* **Headers**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "user_id": 1
  }

OR
JSON

{
  "query": "backend development, PostgreSQL, Flask"
}

    Response (202 Accepted):
    JSON

    {
      "job_id": "725fd211-93e7-4f1f-87b2-d074622226e01",
      "poll_url": "/api/recommend/725fd211-93e7-4f1f-87b2-d074622226e01",
      "status": "processing"
    }

2. Poll Job Status & Retrieve Output

    URL: /api/recommend/<job_id>

    Method: GET

    Response (200 OK):
    JSON

    {
      "job_id": "725fd211-93e7-4f1f-87b2-d074622226e01",
      "status": "completed",
      "data": {
        "user_id": 1,
        "extracted_skills": ["Python", "Machine Learning", "Data Analysis"],
        "recommended_courses": [
          {
            "id": 1,
            "title": "Python for Data Science & Analytics",
            "category": "Data Science",
            "score_percentage": 58.7,
            "matched_skills": ["Python", "Data Analysis"],
            "missing_skills": ["Pandas", "NumPy", "Data Visualization"],
            "explanation": "Matched 2 skill(s) [Python, Data Analysis]. Missing skill gap: [Pandas, NumPy, Data Visualization]."
          }
        ],
        "learning_path": [
          {
            "step": 1,
            "title": "Python for Data Science & Analytics",
            "difficulty": "Beginner",
            "prerequisites": "Basic Computer Literacy"
          }
        ]
      }
    }

3. Recommendation Feedback Loop

    URL: /api/feedback

    Method: POST

    Request Body:
    JSON

    {
      "user_id": 1,
      "course_id": 2,
      "action": "relevant"
    }

    (Supported actions: relevant, not_relevant, saved, enrolled)

4. RAG Course Knowledge Assistant

    URL: /api/rag/qa?course_id=1&question=What+are+the+prerequisites

    Method: GET

    Response (200 OK):
    JSON

    {
      "course_id": 1,
      "course_title": "Python for Data Science & Analytics",
      "question": "What are the prerequisites",
      "answer": "To excel in 'Python for Data Science & Analytics', prerequisites needed: Basic Computer Literacy."
    }

💻 Local Setup & Execution

    Activate Virtual Environment:
    Bash

    source venv/bin/activate

    Install Dependencies:
    Bash

    pip install -r requirements.txt

    Run Application:
    Bash

    python3 app.py

    Access UI:
    Open browser at http://127.0.0.1:5000/recommendation.


