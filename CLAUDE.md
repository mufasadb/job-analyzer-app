# Job Analyzer Application

A full-stack application for analyzing LinkedIn job postings and managing work history for resume building.

## Architecture

### Backend (Django + Supabase)
- **Port**: 5007
- **URL**: http://127.0.0.1:5007
- **API Base**: http://127.0.0.1:5007/api
- **Database**: Local Supabase PostgreSQL (port 54322)

### Frontend (React TypeScript)
- **Port**: 3007  
- **URL**: http://127.0.0.1:3007
- **Framework**: Create React App with TypeScript

### External Services
- **Supabase Local**: http://127.0.0.1:54321
- **Supabase Studio**: http://127.0.0.1:54323
- **OpenRouter API**: GPT-5 Chat for job analysis

## Quick Start

### Start Backend (Django)
```bash
cd backend
source venv/bin/activate
python start_server.py
# OR: python manage.py runserver 127.0.0.1:5007
```

### Start Frontend (React)
```bash
cd frontend
./start_frontend.sh
# OR: PORT=3007 npm start
```

### Start Supabase
```bash
./supabase-cli start
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile

### Job Analysis
- `POST /api/jobs/analyze/` - Analyze LinkedIn job URL
- `GET /api/jobs/history/` - Get analyzed jobs history
- `GET /api/jobs/{id}/` - Get specific job analysis

### Job History Management
- `GET /api/jobs/job-history/` - List user's work history
- `POST /api/jobs/job-history/` - Create new job history
- `GET /api/jobs/job-history/{id}/` - Get specific job with experiences
- `PUT /api/jobs/job-history/{id}/` - Update job history
- `DELETE /api/jobs/job-history/{id}/` - Delete job history

### Experience Management
- `GET /api/jobs/job-history/{job-id}/experiences/` - List experiences for specific job
- `POST /api/jobs/job-history/{job-id}/experiences/` - Create experience for specific job
- `GET /api/jobs/experiences/` - List all user's experiences
- `GET /api/jobs/experiences/{id}/` - Get specific experience
- `PUT /api/jobs/experiences/{id}/` - Update experience
- `DELETE /api/jobs/experiences/{id}/` - Delete experience
- `POST /api/jobs/experiences/enhance/` - AI-enhance experience description

### User Feedback Management
- `GET /api/jobs/feedback/` - List user's feedback (supports filtering by type, priority, implementation status)
- `POST /api/jobs/feedback/` - Create new feedback
- `GET /api/jobs/feedback/{id}/` - Get specific feedback
- `PUT /api/jobs/feedback/{id}/` - Update feedback
- `DELETE /api/jobs/feedback/{id}/` - Delete feedback
- `GET /api/jobs/feedback/stats/` - Get feedback statistics and metrics

## Database Models

### SearchedJob
- LinkedIn URL analysis results
- Job recommendations from AI analysis
- Linked to user

### JobHistory
- User's work history
- job_title, company, start_date, end_date, is_current
- One-to-many with Experience

### Experience  
- Individual achievements/experiences at jobs
- title, description, impact, skills_used
- For cherry-picking resume content

### UserFeedback
- User feedback and notes on resumes/cover letters
- feedback_type (resume, cover_letter, general), title, content
- priority (low, medium, high, critical), is_implemented
- implementation_notes, tags for categorization
- Many-to-one relationship with User

## Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL (via Supabase)
- **AI**: OpenRouter GPT-5 Chat
- **Frontend**: React 18, TypeScript, Axios
- **Authentication**: Token-based
- **Development**: Local Supabase stack

## Environment Variables

### Backend (.env)
```
OPENROUTER_API_KEY=sk-or-v1-[key]
```

### Frontend (.env)
```
PORT=3007
REACT_APP_API_URL=http://127.0.0.1:5007/api
```

## Development Notes

- CORS configured for port 3007
- All APIs require authentication except register/login
- Filtering and search enabled on most endpoints
- Date validation for job history
- User ownership validation on all operations

## Testing

### Test User
A test user is available for development and testing:
- **Username**: `testuser`
- **Password**: `testpass123`
- **Email**: `test@example.com`

```bash
# Create/show test user info
python manage.py create_test_user

# Reset test user (delete and recreate)
python manage.py create_test_user --reset
```