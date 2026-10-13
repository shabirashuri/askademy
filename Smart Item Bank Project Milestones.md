# Smart Item Bank: Project Milestones

Build plan for a React frontend, a FastAPI backend, and AI pipelines built with LangChain and LangGraph (Python).

## Overview

These four milestones each end with something that can be demonstrated. The plan assumes PostgreSQL as the database, because pgvector also supports semantic search later. MySQL from the original prototype document works too, but a separate vector store would then be needed.

## Milestone 1: Foundation, Auth and Course Structure

**Goal:** a working skeleton where users log in and teachers organize courses and topics.

**Backend**

- FastAPI project structure with a database layer (SQLAlchemy and Alembic migrations).
- JWT authentication and role-based access (Admin, Teacher, Student).
- Course and topic CRUD endpoints.

**Frontend**

- React app (Vite) with routing, a login page and a role-based dashboard shell.
- Teacher screens for creating and managing courses and topics.

**Material upload**

- Upload endpoint for PDF, PPTX and DOCX with file validation and storage, linked to a course and topic.

**Setup**

- Docker Compose for the API and database, environment config, and a Git repo with CI basics.

**Demo:** a teacher logs in, creates "Database Systems → SQL Joins" and uploads a lecture file.

## Milestone 2: AI Question Generation Pipeline and Item Bank

**Goal:** the core of the product, turning course material into reviewed, reusable questions.

**Text extraction**

- Parsers for PDF, PPTX and DOCX (LangChain document loaders), then cleaning and chunking by topic.

**LangGraph generation workflow**

- Nodes: load material, chunk, generate MCQs and short questions, validate (format, one correct answer, answerable from the source), remove duplicates, then a human review step.
- Use a LangGraph checkpointer and interrupt so the pipeline pauses for teacher approval and resumes after.
- Use structured output (Pydantic schemas) so every question has a consistent shape: stem, options, answer, explanation, difficulty.

**Teacher-written questions**

- A manual create-question form that saves into the same bank.

**Review and item bank**

- A review screen to edit, reject or accept generated questions.
- Question search and filter by course, topic and type.

**AI plumbing**

- An LLM provider setting, prompt templates kept in one place, and logging of AI runs for debugging and cost tracking.

**Demo:** upload a lecture PDF, generate 20 MCQs, review and save 12, add 5 manual questions, then search the bank.

## Milestone 3: Quizzes, Word Export and Student Attempts

**Goal:** finish the assessment workflow from question bank to student result.

**Quiz/exam builder**

- Select questions from the bank (AI and manual mixed), set title, duration and availability window, and assign to a course.

**Word export**

- A backend service (python-docx) that turns selected questions into a formatted DOCX, with an optional answer key.

**Student side**

- Assigned quiz list and a quiz-taking screen with a timer and autosave of answers.
- Submission and auto-grading for MCQs.
- Result view for students and a results table for teachers.

**AI-assisted grading (optional)**

- A small LangGraph workflow that scores short answers against a reference answer, with the teacher able to override.

**Demo:** a teacher builds a 10-question quiz and exports it to Word, and a student takes the online version and sees a score.

## Milestone 4: Student Search, Teacher Insights and Release Readiness

**Goal:** the feature that makes the idea different, the student-to-teacher feedback loop, plus hardening.

**Smart student search**

- Embed course content and questions into a vector store (pgvector) for semantic search.
- A search endpoint that returns results and logs each search (student, text, course/topic, time) without slowing the response.

**Teacher insights dashboard**

- Filters by course, topic, student and date.
- A LangGraph analytics workflow that clusters similar searches (for example "LEFT JOIN" and "left outer join") and ranks the most-requested topics.
- A suggested action list, such as "Students keep searching LEFT JOIN, so generate 5 more questions", with a one-click button into the generation pipeline from Milestone 2.

**Hardening**

- Role and permission tests.
- Rate limiting and error handling on AI calls.
- Input and file-upload security checks.
- Backend tests (pytest) and basic frontend tests.

**Deployment**

- Production Docker setup, deployed staging environment, monitoring, and a user guide for teachers.

**Demo:** students search SQL topics, the teacher sees LEFT JOIN flagged as a repeated need, and one click generates new questions for it.

## Notes

- **Dependencies:** each milestone builds on the previous one. Milestone 2 carries the most technical risk, so give it the most time.
- **Rough effort** for one or two developers: about 3 to 4 weeks for Milestone 1, 4 to 5 for Milestone 2, 3 to 4 for Milestone 3 and 3 to 4 for Milestone 4. Adjust for team size.
- **Decide early:** which LLM provider to use, file storage (local or cloud), and whether students sign up themselves or teachers enroll them.
