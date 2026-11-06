from datetime import date,datetime
from typing import Literal,Optional
from pydantic import BaseModel,ConfigDict,EmailStr,Field
Cat=Literal["Cardio","Strength","Yoga"]
class Register(BaseModel):
 username:str=Field(min_length=3,max_length=50); email:EmailStr; password:str=Field(min_length=6,max_length=72)
class Login(BaseModel):
 username_or_email:str; password:str
class UserOut(BaseModel):
 id:int; username:str; email:EmailStr; created_at:datetime
 model_config=ConfigDict(from_attributes=True)
class WorkoutIn(BaseModel):
 workout_name:str=Field(min_length=1,max_length=120); category:Cat; duration:int=Field(gt=0,le=1440); calories_burned:float=Field(ge=0); workout_date:date
class GoalIn(BaseModel):
 goal_type:Literal["Weight Loss","Muscle Gain","Steps"]; target_value:float=Field(gt=0); current_value:float=Field(default=0,ge=0); deadline:date
class GoalPatch(BaseModel):
 current_value:Optional[float]=Field(default=None,ge=0); status:Optional[Literal["ACTIVE","COMPLETED","PAUSED"]]=None
class PlanIn(BaseModel):
 title:str=Field(min_length=1,max_length=120); description:str=""; scheduled_date:date
class ExerciseIn(BaseModel):
 name:str; category:Cat; description:str=""; duration:int=Field(gt=0,le=1440)
