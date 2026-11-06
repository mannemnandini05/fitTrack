# FitTrack — Combined Phase 1 + Phase 2

## Coverage checklist

**Phase 1:** user registration/login, bcrypt password hashing, JWT authentication, protected APIs, ownership validation, workout create/list/edit/delete, daily progress totals, goals create/list/update/delete, weekly and monthly reports, calories analytics, chart, notifications and mark-as-read, Pydantic validation, environment configuration.

**Phase 2:** workout plans create/list/upcoming filter/delete, calendar-style scheduled date list, seeded searchable exercise library and add exercise to workout, weekly/monthly comparison and trends, current/longest streak and missed-day reset, milestone badges (first workout, 10 workouts, 7-day and 30-day streak), personalized dashboard with daily summary/upcoming plans/goals/streak/badge count.

## Run backend (PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Swagger: http://127.0.0.1:8000/docs

## Run frontend (second terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open the Vite URL, normally http://localhost:5173.

Register a new user on the UI, then login. Database `backend/fittrack.db` is created automatically. The API uses the logged-in JWT user ID to scope every personal record. Set a strong `SECRET_KEY` and restrict CORS before deployment.

## Notes
- Python 3.10+ recommended.
- Notifications are generated for workout saves, goal creation/completion, and earned badges. A scheduled background worker for daily reminders is not included; daily reminder delivery requires a scheduler/worker deployment.
- The exercise library is pre-seeded with Cardio, Strength and Yoga examples. Users can search and add an exercise to the workout form.
