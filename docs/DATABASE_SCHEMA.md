# Database Schema

## Users Table
- id: UUID (Primary Key)
- email: String (Unique)
- password_hash: String
- first_name: String
- last_name: String
- created_at: DateTime
- updated_at: DateTime

## Resumes Table
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key)
- file_path: String
- parsed_content: JSON
- created_at: DateTime
- updated_at: DateTime

## Jobs Table
- id: UUID (Primary Key)
- title: String
- company: String
- description: String
- requirements: String
- salary_range: String
- source: String (RapidAPI, Adzuna, etc.)
- created_at: DateTime

## Match History Table
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key)
- resume_id: UUID (Foreign Key)
- job_id: UUID (Foreign Key)
- match_score: Float
- created_at: DateTime
