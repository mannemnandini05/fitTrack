
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models as m
from .database import Base, engine, get_db
from .security import (
    hash_password,
    verify_password,
    create_token,
    token_user_id,
)

# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FitTrack Fitness API",
    description="Fitness and Workout Management Platform - Phase 1 and Phase 2",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# AUTHENTICATION DEPENDENCIES
# --------------------------------------------------

def get_current_user(
    token: str,
    db: Session,
):
    try:
        user_id = token_user_id(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user = db.query(m.User).filter(m.User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    return get_current_user(credentials.credentials, db)


def get_owned_record(model, record_id, user_id, db):
    record = db.query(model).filter(
        model.id == record_id,
        model.user_id == user_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Record not found",
        )

    return record


# --------------------------------------------------
# PYDANTIC SCHEMAS
# --------------------------------------------------

class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class LoginInput(BaseModel):
    username_or_email: str
    password: str


class WorkoutInput(BaseModel):
    workout_name: str
    category: str
    duration: int = Field(gt=0)
    calories_burned: float = Field(ge=0)
    workout_date: date


class GoalInput(BaseModel):
    goal_type: str
    target_value: float = Field(gt=0)
    current_value: float = Field(ge=0)
    deadline: date


class WorkoutPlanInput(BaseModel):
    title: str
    description: Optional[str] = None
    scheduled_date: date


class ExerciseInput(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    duration: int = Field(gt=0)


class NotificationInput(BaseModel):
    title: str
    message: str


# --------------------------------------------------
# GENERAL HELPERS
# --------------------------------------------------

def validate_category(category):
    if category not in ["Cardio", "Strength", "Yoga"]:
        raise HTTPException(
            status_code=422,
            detail="Category must be Cardio, Strength, or Yoga",
        )


def update_fields(record, data):
    for key, value in data.items():
        if hasattr(record, key):
            setattr(record, key, value)


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to FitTrack Fitness API",
        "phase": "Phase 1 and Phase 2",
        "documentation": "/docs",
    }


# --------------------------------------------------
# MODULE 1: USER AUTHENTICATION
# --------------------------------------------------

@app.post("/auth/register", status_code=201)
def register(
    data: RegisterInput,
    db: Session = Depends(get_db),
):
    existing = db.query(m.User).filter(
        (m.User.username == data.username) |
        (m.User.email == data.email)
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )

    user = m.User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "Registration successful",
    }


@app.post("/auth/login")
def login(
    data: LoginInput,
    db: Session = Depends(get_db),
):
    user = db.query(m.User).filter(
        (m.User.username == data.username_or_email) |
        (m.User.email == data.username_or_email)
    ).first()

    if not user or not verify_password(
        data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password",
        )

    token = create_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    }


@app.get("/profile")
def profile(user=Depends(current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


# --------------------------------------------------
# MODULE 2: WORKOUT MANAGEMENT
# --------------------------------------------------

@app.post("/workouts", status_code=201)
def add_workout(
    data: WorkoutInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    validate_category(data.category)

    workout = m.Workout(
        user_id=user.id,
        workout_name=data.workout_name,
        category=data.category,
        duration=data.duration,
        calories_burned=data.calories_burned,
        workout_date=data.workout_date,
    )

    db.add(workout)
    db.commit()
    db.refresh(workout)

    return workout


@app.get("/workouts")
def list_workouts(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return db.query(m.Workout).filter(
        m.Workout.user_id == user.id
    ).all()


@app.get("/workouts/{workout_id}")
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return get_owned_record(
        m.Workout, workout_id, user.id, db
    )


@app.put("/workouts/{workout_id}")
def update_workout(
    workout_id: int,
    data: WorkoutInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    validate_category(data.category)

    workout = get_owned_record(
        m.Workout, workout_id, user.id, db
    )

    update_fields(workout, data.model_dump())
    db.commit()
    db.refresh(workout)

    return workout


@app.delete("/workouts/{workout_id}")
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    workout = get_owned_record(
        m.Workout, workout_id, user.id, db
    )

    db.delete(workout)
    db.commit()

    return {"message": "Workout deleted successfully"}


# --------------------------------------------------
# MODULE 3: DAILY PROGRESS TRACKING
# --------------------------------------------------

@app.get("/progress/daily")
def daily_progress(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    today = date.today()

    workouts = db.query(m.Workout).filter(
        m.Workout.user_id == user.id,
        m.Workout.workout_date == today,
    ).all()

    return {
        "date": today,
        "total_workouts": len(workouts),
        "total_calories": sum(
            w.calories_burned for w in workouts
        ),
        "total_duration": sum(
            w.duration for w in workouts
        ),
    }


# --------------------------------------------------
# MODULE 4: GOAL MANAGEMENT
# --------------------------------------------------

@app.post("/goals", status_code=201)
def create_goal(
    data: GoalInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    if data.goal_type not in [
        "Weight Loss", "Muscle Gain", "Steps"
    ]:
        raise HTTPException(
            status_code=422,
            detail="Invalid goal type",
        )

    goal = m.Goal(
        user_id=user.id,
        goal_type=data.goal_type,
        target_value=data.target_value,
        current_value=data.current_value,
        deadline=data.deadline,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@app.get("/goals")
def list_goals(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return db.query(m.Goal).filter(
        m.Goal.user_id == user.id
    ).all()


@app.put("/goals/{goal_id}")
def update_goal(
    goal_id: int,
    data: GoalInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    goal = get_owned_record(
        m.Goal, goal_id, user.id, db
    )

    update_fields(goal, data.model_dump())
    db.commit()
    db.refresh(goal)

    completed = goal.current_value >= goal.target_value

    return {
        "goal": goal,
        "completed": completed,
        "message": "Goal completed" if completed else "Goal updated",
    }


@app.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    goal = get_owned_record(
        m.Goal, goal_id, user.id, db
    )

    db.delete(goal)
    db.commit()

    return {"message": "Goal deleted successfully"}


# --------------------------------------------------
# MODULE 5: REPORTS AND ANALYTICS
# --------------------------------------------------

@app.get("/reports/weekly")
def weekly_report(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    start = date.today() - timedelta(days=6)

    workouts = db.query(m.Workout).filter(
        m.Workout.user_id == user.id,
        m.Workout.workout_date >= start,
        m.Workout.workout_date <= date.today(),
    ).all()

    return {
        "period": "Weekly",
        "total_workouts": len(workouts),
        "total_calories": sum(
            w.calories_burned for w in workouts
        ),
        "total_duration": sum(
            w.duration for w in workouts
        ),
    }


@app.get("/reports/monthly")
def monthly_report(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    today = date.today()
    start = today.replace(day=1)

    workouts = db.query(m.Workout).filter(
        m.Workout.user_id == user.id,
        m.Workout.workout_date >= start,
        m.Workout.workout_date <= today,
    ).all()

    return {
        "period": "Monthly",
        "total_workouts": len(workouts),
        "total_calories": sum(
            w.calories_burned for w in workouts
        ),
        "total_duration": sum(
            w.duration for w in workouts
        ),
    }


# --------------------------------------------------
# MODULE 6: NOTIFICATIONS
# --------------------------------------------------

@app.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return db.query(m.Notification).filter(
        m.Notification.user_id == user.id
    ).order_by(m.Notification.created_at.desc()).all()


@app.post("/notifications", status_code=201)
def add_notification(
    data: NotificationInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    notification = m.Notification(
        user_id=user.id,
        title=data.title,
        message=data.message,
        is_read=False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


@app.patch("/notifications/{nid}/read")
def read_notification(
    nid: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    notification = get_owned_record(
        m.Notification, nid, user.id, db
    )

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@app.post("/notifications/reminders")
def create_reminder(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    notification = m.Notification(
        user_id=user.id,
        title="Daily Workout Reminder",
        message="Complete your daily workout and stay fit!",
        is_read=False,
    )

    db.add(notification)
    db.commit()

    return {"message": "Workout reminder created"}


# --------------------------------------------------
# MODULE 7: WORKOUT PLANS AND SCHEDULING
# --------------------------------------------------

@app.post("/workout-plans", status_code=201)
def create_workout_plan(
    data: WorkoutPlanInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    plan = m.WorkoutPlan(
        user_id=user.id,
        title=data.title,
        description=data.description,
        scheduled_date=data.scheduled_date,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@app.get("/workout-plans")
def list_workout_plans(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return db.query(m.WorkoutPlan).filter(
        m.WorkoutPlan.user_id == user.id
    ).order_by(m.WorkoutPlan.scheduled_date).all()


@app.get("/workout-plans/upcoming")
def upcoming_workouts(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    return db.query(m.WorkoutPlan).filter(
        m.WorkoutPlan.user_id == user.id,
        m.WorkoutPlan.scheduled_date >= date.today(),
    ).order_by(m.WorkoutPlan.scheduled_date).all()


@app.put("/workout-plans/{plan_id}")
def update_workout_plan(
    plan_id: int,
    data: WorkoutPlanInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    plan = get_owned_record(
        m.WorkoutPlan, plan_id, user.id, db
    )

    update_fields(plan, data.model_dump())
    db.commit()
    db.refresh(plan)

    return plan


@app.delete("/workout-plans/{plan_id}")
def delete_workout_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    plan = get_owned_record(
        m.WorkoutPlan, plan_id, user.id, db
    )

    db.delete(plan)
    db.commit()

    return {"message": "Workout plan deleted"}


# --------------------------------------------------
# MODULE 8: EXERCISE LIBRARY
# --------------------------------------------------

@app.post("/exercises", status_code=201)
def add_exercise(
    data: ExerciseInput,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    validate_category(data.category)

    exercise = m.Exercise(
        name=data.name,
        category=data.category,
        description=data.description,
        duration=data.duration,
    )

    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    return exercise


@app.get("/exercises")
def list_exercises(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    query = db.query(m.Exercise)

    if search:
        query = query.filter(
            m.Exercise.name.ilike(f"%{search}%")
        )

    if category:
        validate_category(category)
        query = query.filter(
            m.Exercise.category == category
        )

    return query.all()


# --------------------------------------------------
# MODULE 9: PROGRESS COMPARISON
# --------------------------------------------------

@app.get("/progress/compare/weekly")
def compare_weekly_progress(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    today = date.today()
    this_start = today - timedelta(days=6)
    previous_start = today - timedelta(days=13)
    previous_end = today - timedelta(days=7)

    def calculate(start, end):
        records = db.query(m.Workout).filter(
            m.Workout.user_id == user.id,
            m.Workout.workout_date >= start,
            m.Workout.workout_date <= end,
        ).all()

        return {
            "workouts": len(records),
            "calories": sum(
                w.calories_burned for w in records
            ),
            "duration": sum(
                w.duration for w in records
            ),
        }

    return {
        "current_week": calculate(this_start, today),
        "previous_week": calculate(previous_start, previous_end),
    }


@app.get("/progress/compare/monthly")
def compare_monthly_progress(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    today = date.today()
    current_start = today.replace(day=1)

    previous_last = current_start - timedelta(days=1)
    previous_start = previous_last.replace(day=1)

    def calculate(start, end):
        records = db.query(m.Workout).filter(
            m.Workout.user_id == user.id,
            m.Workout.workout_date >= start,
            m.Workout.workout_date <= end,
        ).all()

        return {
            "workouts": len(records),
            "calories": sum(
                w.calories_burned for w in records
            ),
            "duration": sum(
                w.duration for w in records
            ),
        }

    return {
        "current_month": calculate(current_start, today),
        "previous_month": calculate(previous_start, previous_last),
    }


# --------------------------------------------------
# MODULE 10: STREAK TRACKING
# --------------------------------------------------

@app.get("/streak")
def get_streak(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    streak = db.query(m.Streak).filter(
        m.Streak.user_id == user.id
    ).first()

    if not streak:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_workout_date": None,
        }

    if (
        streak.last_workout_date
        and streak.last_workout_date < date.today() - timedelta(days=1)
    ):
        streak.current_streak = 0
        db.commit()

    return {
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "last_workout_date": streak.last_workout_date,
    }


# --------------------------------------------------
# MODULE 11: ACHIEVEMENT BADGES
# --------------------------------------------------

@app.get("/badges")
def list_badges(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    records = db.query(
        m.Badge, m.UserBadge
    ).join(
        m.UserBadge,
        m.Badge.id == m.UserBadge.badge_id
    ).filter(
        m.UserBadge.user_id == user.id
    ).all()

    return [
        {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "icon": badge.icon,
            "earned_at": user_badge.earned_at,
        }
        for badge, user_badge in records
    ]


# --------------------------------------------------
# MODULE 12: PERSONALIZED DASHBOARD
# --------------------------------------------------

@app.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    today = date.today()
    week_start = today - timedelta(days=6)

    today_workouts = db.query(m.Workout).filter(
        m.Workout.user_id == user.id,
        m.Workout.workout_date == today,
    ).all()

    weekly_workouts = db.query(m.Workout).filter(
        m.Workout.user_id == user.id,
        m.Workout.workout_date >= week_start,
        m.Workout.workout_date <= today,
    ).all()

    upcoming = db.query(m.WorkoutPlan).filter(
        m.WorkoutPlan.user_id == user.id,
        m.WorkoutPlan.scheduled_date >= today,
    ).order_by(m.WorkoutPlan.scheduled_date).limit(5).all()

    goals = db.query(m.Goal).filter(
        m.Goal.user_id == user.id
    ).all()

    streak = db.query(m.Streak).filter(
        m.Streak.user_id == user.id
    ).first()

    earned_badges = db.query(m.UserBadge).filter(
        m.UserBadge.user_id == user.id
    ).count()

    return {
        "username": user.username,
        "date": today,
        "daily_summary": {
            "total_workouts": len(today_workouts),
            "calories_burned": sum(
                w.calories_burned for w in today_workouts
            ),
            "active_minutes": sum(
                w.duration for w in today_workouts
            ),
        },
        "weekly_summary": {
            "total_workouts": len(weekly_workouts),
            "total_calories": sum(
                w.calories_burned for w in weekly_workouts
            ),
        },
        "upcoming_workouts": upcoming,
        "goals": goals,
        "streak": {
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
        },
        "earned_badges": earned_badges,
    }


# --------------------------------------------------
# APPLICATION STARTUP
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "FitTrack API is running"}
