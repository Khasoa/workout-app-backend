from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from sqlalchemy import CheckConstraint
from datetime import date as date_type
 
db = SQLAlchemy()

# ── Exercise ──
# Reusable exercises a trainer can attach to many workouts.
 
class Exercise(db.Model):
    __tablename__ = "exercises"
 
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String,  nullable=False, unique=True)  # TABLE CONSTRAINT 1 + 2
    category         = db.Column(db.String,  nullable=False)               # TABLE CONSTRAINT 3
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)
 
    # One Exercise -> many WorkoutExercise join rows
    # cascade="all, delete-orphan": deleting an exercise also removes its join rows
    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan"
    )
 
    # ── Model Validations ──
 
    VALID_CATEGORIES = ["strength", "cardio", "flexibility", "balance", "core"]
 
    @validates("name")
    def validate_name(self, key, value):
        # MODEL VALIDATION 1: name must be at least 2 non-whitespace characters
        if not value or len(value.strip()) < 2:
            raise ValueError("Exercise name must be at least 2 characters")
        return value.strip()
 
    @validates("category")
    def validate_category(self, key, value):
        # MODEL VALIDATION 2: only accepted categories are allowed
        if value not in self.VALID_CATEGORIES:
            raise ValueError(f"Category must be one of: {self.VALID_CATEGORIES}")
        return value
 
 
# ── Workout ──
# A single training session: date, duration, optional notes.
 
class Workout(db.Model):
    __tablename__ = "workouts"
 
    id               = db.Column(db.Integer, primary_key=True)
    date             = db.Column(db.Date,    nullable=False)    # TABLE CONSTRAINT 4: db.Date not String
    duration_minutes = db.Column(db.Integer, nullable=False)    # TABLE CONSTRAINT 5
    notes            = db.Column(db.Text)
 
    # One Workout -> many WorkoutExercise join rows
    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan"
    )
 
    # ── Model Validations ───
 
    @validates("duration_minutes")
    def validate_duration(self, key, value):
        # MODEL VALIDATION 3: duration must be a positive number
        if value is None or value <= 0:
            raise ValueError("Duration must be greater than 0")
        return value
 
    @validates("date")
    def validate_date(self, key, value):
        # MODEL VALIDATION 4: workout date cannot be in the future
        if isinstance(value, date_type) and value > date_type.today():
            raise ValueError("Workout date cannot be in the future")
        return value
 
 
# ── WorkoutExercise (Join Table) ──
# Links a Workout to an Exercise and stores the actual work done:
# reps, sets, and/or duration for that exercise in that session.

 
class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
 
    id               = db.Column(db.Integer, primary_key=True)
    workout_id       = db.Column(db.Integer, db.ForeignKey("workouts.id"),  nullable=False)
    exercise_id      = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    reps             = db.Column(db.Integer, default=None)
    sets             = db.Column(db.Integer, default=None)
    duration_seconds = db.Column(db.Integer, default=None)
 
    # back_populates must match the relationship name on the other side exactly
    workout  = db.relationship("Workout",  back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")
 
    # TABLE CONSTRAINTS 6-8: DB-level check prevents negative values
    __table_args__ = (
        CheckConstraint("reps IS NULL OR reps >= 0",             name="check_reps_non_negative"),
        CheckConstraint("sets IS NULL OR sets >= 0",             name="check_sets_non_negative"),
        CheckConstraint("duration_seconds IS NULL OR duration_seconds >= 0",
                        name="check_duration_non_negative"),
    )