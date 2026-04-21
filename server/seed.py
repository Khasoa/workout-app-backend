#!/usr/bin/env python3
# Run with: python server/seed.py  (from the project root)
 
from app import app
from models import db, Workout, Exercise, WorkoutExercise
from datetime import date
 
with app.app_context():
 
    # ── Reset ─────────────────────────────────────────────────────────────────
    # Delete join rows first (they reference both parent tables via FK),
    # then parents. This respects FK constraints without dropping tables,
    # so your migration history stays intact.
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()
 
    # ── Exercises ─────────────────────────────────────────────────────────────
    squat   = Exercise(name="Squat",       category="strength",    equipment_needed=False)
    deadlft = Exercise(name="Deadlift",    category="strength",    equipment_needed=True)
    row_ex  = Exercise(name="Rowing",      category="cardio",      equipment_needed=True)
    plank   = Exercise(name="Plank",       category="core",        equipment_needed=False)
    stretch = Exercise(name="Hip Stretch", category="flexibility", equipment_needed=False)
 
    db.session.add_all([squat, deadlft, row_ex, plank, stretch])
    db.session.commit()  # commit before WorkoutExercises so IDs are assigned
 
    # ── Workouts ──────────────────────────────────────────────────────────────
    # date= expects a Python date object because the column type is db.Date
    w1 = Workout(date=date(2024, 4, 1),  duration_minutes=60, notes="Leg day")
    w2 = Workout(date=date(2024, 4, 3),  duration_minutes=45, notes="Cardio and core")
    w3 = Workout(date=date(2024, 4, 5),  duration_minutes=30, notes="Recovery session")
 
    db.session.add_all([w1, w2, w3])
    db.session.commit()
 
    # ── WorkoutExercises ──────────────────────────────────────────────────────
    # Each row links one workout to one exercise and records the work done.
    db.session.add_all([
        WorkoutExercise(workout_id=w1.id, exercise_id=squat.id,   sets=4, reps=12),
        WorkoutExercise(workout_id=w1.id, exercise_id=deadlft.id, sets=3, reps=8),
        WorkoutExercise(workout_id=w2.id, exercise_id=row_ex.id,  sets=1, duration_seconds=1200),
        WorkoutExercise(workout_id=w2.id, exercise_id=plank.id,   sets=3, duration_seconds=60),
        WorkoutExercise(workout_id=w3.id, exercise_id=stretch.id, sets=2, duration_seconds=90),
    ])
    db.session.commit()
 
    print("Seeded: 5 exercises | 3 workouts | 5 workout_exercise links")