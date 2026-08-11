from sqlalchemy.sql import insert
import db

def seed_database():
    # 1. Drop all existing tables to refresh the schema with new Level 3 columns
    print("Dropping old database schema...")
    db.metadata.drop_all(db.engine)

    # 2. Re-create all tables with updated schema (prerequisites, topics, difficulty, jobs, user_feedback)
    print("Creating fresh database tables with Level 3 schema...")
    db.metadata.create_all(db.engine)

    with db.engine.connect() as conn:
        print("Seeding Expanded Courses Catalog with RAG Metadata...")
        courses_data = [
            {
                "title": "Python for Data Science & Analytics",
                "category": "Data Science",
                "skills": "Python, Data Analysis, Pandas, NumPy, Data Visualization",
                "description": "Master Python basics, data manipulation using Pandas, and visual analytics with Seaborn.",
                "prerequisites": "Basic Computer Literacy",
                "topics": "Python Syntax, DataFrames, Aggregations, Matplotlib Plots",
                "difficulty": "Beginner"
            },
            {
                "title": "Machine Learning Engineering",
                "category": "Artificial Intelligence",
                "skills": "Python, Machine Learning, Scikit-Learn, Statistics, Feature Engineering",
                "description": "Learn predictive modeling, regression, decision trees, and model evaluation pipelines.",
                "prerequisites": "Python, Basic Linear Algebra & Statistics",
                "topics": "Supervised Learning, Classification, Cross-Validation, Hyperparameter Tuning",
                "difficulty": "Intermediate"
            },
            {
                "title": "Deep Learning & Neural Networks",
                "category": "Artificial Intelligence",
                "skills": "Python, PyTorch, Deep Learning, Neural Networks, Computer Vision",
                "description": "Build deep neural architectures, CNNs for image classification, and modern vision pipelines.",
                "prerequisites": "Machine Learning Engineering, Python",
                "topics": "Perceptrons, Backpropagation, CNN Architectures, PyTorch Autograd",
                "difficulty": "Advanced"
            },
            {
                "title": "Full-Stack Web Development with Flask",
                "category": "Web Development",
                "skills": "Python, Flask, HTML, CSS, SQL, REST APIs",
                "description": "Build web applications, write RESTful APIs, and integrate Flask with PostgreSQL backends.",
                "prerequisites": "Python Fundamentals, Basic HTML",
                "topics": "Routing, Jinja2 Templates, SQLAlchemy Core, Session Management, REST Endpoints",
                "difficulty": "Intermediate"
            },
            {
                "title": "Database Architecture & PostgreSQL",
                "category": "Database & Cloud",
                "skills": "SQL, PostgreSQL, Database Design, SQLAlchemy, Alembic",
                "description": "Design relational database schemas, write optimized SQL queries, and manage migrations.",
                "prerequisites": "Basic Database Knowledge",
                "topics": "Entity Relationships, Indexing, Foreign Keys, Alembic Migrations, Joins",
                "difficulty": "Intermediate"
            },
            {
                "title": "Docker & Containerization Fundamentals",
                "category": "DevOps & Cloud",
                "skills": "Docker, DevOps, Containerization, Linux, CI/CD",
                "description": "Learn to containerize Python and Flask web microservices using Docker and Compose.",
                "prerequisites": "Linux CLI basics, Web application concepts",
                "topics": "Dockerfiles, Image Layers, Container Networks, Docker Compose Services",
                "difficulty": "Beginner"
            },
            {
                "title": "Natural Language Processing with Transformers",
                "category": "Artificial Intelligence",
                "skills": "Python, NLP, Transformers, PyTorch, HuggingFace",
                "description": "Explore sentiment analysis, text embeddings, vector similarity search, and LLM fine-tuning.",
                "prerequisites": "Deep Learning & PyTorch",
                "topics": "Tokenization, Self-Attention Mechanisms, SentenceTransformers, Vector Embeddings",
                "difficulty": "Advanced"
            }
        ]
        
        for c in courses_data:
            conn.execute(insert(db.courses).values(**c))

        print("Seeding Registered Users...")
        users_data = [
            {"name": "Mohamed Mustafa", "email": "mohamed@example.com"},
            {"name": "Haya Abu Shawish", "email": "haya@example.com"},
            {"name": "Tareq Munther", "email": "tareq@example.com"},
            {"name": "Abdelrahman Tayseer", "email": "abdelrahman@example.com"},
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"}
        ]

        user_ids = {}
        for u in users_data:
            result = conn.execute(insert(db.users).values(**u).returning(db.users.c.id))
            user_ids[u["name"]] = result.fetchone()[0]

        print("Seeding User Profile Skills...")
        user_skills_mapping = [
            {"user_id": user_ids["Mohamed Mustafa"], "skill_name": "Python"},
            {"user_id": user_ids["Mohamed Mustafa"], "skill_name": "Machine Learning"},
            {"user_id": user_ids["Mohamed Mustafa"], "skill_name": "Data Analysis"},

            {"user_id": user_ids["Haya Abu Shawish"], "skill_name": "Flask"},
            {"user_id": user_ids["Haya Abu Shawish"], "skill_name": "Web Development"},
            {"user_id": user_ids["Haya Abu Shawish"], "skill_name": "HTML"},

            {"user_id": user_ids["Tareq Munther"], "skill_name": "PostgreSQL"},
            {"user_id": user_ids["Tareq Munther"], "skill_name": "SQL"},
            {"user_id": user_ids["Tareq Munther"], "skill_name": "Docker"},

            {"user_id": user_ids["Abdelrahman Tayseer"], "skill_name": "Deep Learning"},
            {"user_id": user_ids["Abdelrahman Tayseer"], "skill_name": "PyTorch"},
            {"user_id": user_ids["Abdelrahman Tayseer"], "skill_name": "NLP"},

            {"user_id": user_ids["Alice Johnson"], "skill_name": "Python"},
            {"user_id": user_ids["Alice Johnson"], "skill_name": "Pandas"},

            {"user_id": user_ids["Bob Smith"], "skill_name": "HTML"},
            {"user_id": user_ids["Bob Smith"], "skill_name": "CSS"}
        ]

        for us in user_skills_mapping:
            conn.execute(insert(db.user_skills).values(**us))

        conn.commit()
        print("Database seeded successfully with Level 3 metadata!")

if __name__ == '__main__':
    seed_database()