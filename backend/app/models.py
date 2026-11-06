from datetime import datetime,timezone
from sqlalchemy import Column,Integer,String,Date,DateTime,Float,Boolean,ForeignKey,Text,UniqueConstraint
from .database import Base
now=lambda: datetime.now(timezone.utc)
class User(Base):
 __tablename__="users"
 id=Column(Integer,primary_key=True); username=Column(String(50),unique=True,index=True,nullable=False); email=Column(String(255),unique=True,index=True,nullable=False); hashed_password=Column(String(255),nullable=False); created_at=Column(DateTime(timezone=True),default=now)
class Workout(Base):
 __tablename__="workouts"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),index=True); workout_name=Column(String(120),nullable=False); category=Column(String(20),nullable=False); duration=Column(Integer,nullable=False); calories_burned=Column(Float,default=0); workout_date=Column(Date,nullable=False); created_at=Column(DateTime(timezone=True),default=now)
class Progress(Base):
 __tablename__="progress"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id")); total_workouts=Column(Integer,default=0); total_calories=Column(Float,default=0); date=Column(Date,nullable=False); __table_args__=(UniqueConstraint("user_id","date"),)
class Goal(Base):
 __tablename__="goals"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),index=True); goal_type=Column(String(30)); target_value=Column(Float); current_value=Column(Float,default=0); deadline=Column(Date); status=Column(String(20),default="ACTIVE"); created_at=Column(DateTime(timezone=True),default=now)
class Notification(Base):
 __tablename__="notifications"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),index=True); title=Column(String(160)); message=Column(Text); is_read=Column(Boolean,default=False); created_at=Column(DateTime(timezone=True),default=now)
class WorkoutPlan(Base):
 __tablename__="workout_plans"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),index=True); title=Column(String(120)); description=Column(Text,default=""); scheduled_date=Column(Date); created_at=Column(DateTime(timezone=True),default=now)
class Exercise(Base):
 __tablename__="exercises"
 id=Column(Integer,primary_key=True); name=Column(String(120),unique=True); category=Column(String(20)); description=Column(Text,default=""); duration=Column(Integer)
class Streak(Base):
 __tablename__="streaks"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),unique=True); current_streak=Column(Integer,default=0); longest_streak=Column(Integer,default=0); last_workout_date=Column(Date)
class Badge(Base):
 __tablename__="badges"
 id=Column(Integer,primary_key=True); name=Column(String(80),unique=True); description=Column(Text); icon=Column(String(40),default="🏅")
class UserBadge(Base):
 __tablename__="user_badges"
 id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey("users.id"),index=True); badge_id=Column(Integer,ForeignKey("badges.id")); earned_at=Column(DateTime(timezone=True),default=now); __table_args__=(UniqueConstraint("user_id","badge_id"),)
