from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from marshmallow import ValidationError
 
from models import db, Workout, Exercise, WorkoutExercise
from schemas import (
    exercise_schema, exercises_schema,
    workout_schema, workouts_schema,
    workout_exercise_schema
)
 
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
 
db.init_app(app)
Migrate(app, db)
 
 
# ── Helpers ──
 
def schema_error(e):
    """422 response for marshmallow ValidationError — invalid request body."""
    return jsonify({"errors": e.messages}), 422
 
def model_error(e):
    """422 response for ValueError raised by @validates in models."""
    return jsonify({"error": str(e)}), 422
 
 
# ── Health check ──
 
@app.route("/")
def home():
    return jsonify({"message": "Workout API is running"}), 200
 
 
# ── Exercise Routes ──
 
@app.route("/exercises", methods=["GET"])
def get_exercises():
    """Return a list of all exercises."""
    return jsonify(exercises_schema.dump(Exercise.query.all())), 200
 
 
@app.route("/exercises/<int:id>", methods=["GET"])
def get_exercise(id):
    """Return a single exercise. 404 if not found."""
    return jsonify(exercise_schema.dump(Exercise.query.get_or_404(id))), 200
 
 
@app.route("/exercises", methods=["POST"])
def create_exercise():
    """
    Create a new exercise.
    Required body: { "name": str, "category": str }
    Optional body: { "equipment_needed": bool }  -- defaults to false
    """
    try:
        # schema.load() validates the body; raises ValidationError on bad data
        data     = exercise_schema.load(request.get_json())
        exercise = Exercise(**data)
        db.session.add(exercise)
        db.session.commit()
        return jsonify(exercise_schema.dump(exercise)), 201
    except ValidationError as e:
        return schema_error(e)
    except ValueError as e:
        # raised by @validates decorators in the model
        return model_error(e)
 
 
@app.route("/exercises/<int:id>", methods=["DELETE"])
def delete_exercise(id):
    """
    Delete an exercise and its associated WorkoutExercise rows.
    cascade="all, delete-orphan" on the relationship handles the join rows automatically.
    Returns 204 No Content — the REST standard for a successful DELETE.
    """
    exercise = Exercise.query.get_or_404(id)
    db.session.delete(exercise)
    db.session.commit()
    return make_response("", 204)
 
 
# ── Workout Routes ──
 
@app.route("/workouts", methods=["GET"])
def get_workouts():
    """Return a list of all workouts."""
    return jsonify(workouts_schema.dump(Workout.query.all())), 200
 
 
@app.route("/workouts/<int:id>", methods=["GET"])
def get_workout(id):
    """
    Return a single workout with nested workout_exercises (each includes exercise details).
    This satisfies the stretch goal: reps/sets/duration data is embedded in the response.
    """
    return jsonify(workout_schema.dump(Workout.query.get_or_404(id))), 200
 
 
@app.route("/workouts", methods=["POST"])
def create_workout():
    """
    Create a new workout.
    Required body: { "date": "YYYY-MM-DD", "duration_minutes": int }
    Optional body: { "notes": str }
    """
    try:
        data    = workout_schema.load(request.get_json())
        workout = Workout(**data)
        db.session.add(workout)
        db.session.commit()
        return jsonify(workout_schema.dump(workout)), 201
    except ValidationError as e:
        return schema_error(e)
    except ValueError as e:
        return model_error(e)
 
 
@app.route("/workouts/<int:id>", methods=["DELETE"])
def delete_workout(id):
    """
    Delete a workout and its associated WorkoutExercise rows.
    cascade="all, delete-orphan" handles the join rows automatically.
    """
    workout = Workout.query.get_or_404(id)
    db.session.delete(workout)
    db.session.commit()
    return make_response("", 204)
 
 
# ── WorkoutExercise Route ──
 
@app.route(
    "/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises",
    methods=["POST"]
)
def add_exercise_to_workout(workout_id, exercise_id):
    """
    Link an exercise to a workout with optional tracking data.
    - workout_id and exercise_id come from the URL (not the body).
    - Body (all optional): { "sets": int, "reps": int, "duration_seconds": int }
    - Returns 404 if either parent record does not exist.
    """
    # Confirm both parent records exist before creating the join row
    Workout.query.get_or_404(workout_id)
    Exercise.query.get_or_404(exercise_id)
 
    try:
        # Empty body is valid — all fields are optional (load_default=None in schema)
        data = workout_exercise_schema.load(request.get_json() or {})
    except ValidationError as e:
        return schema_error(e)
 
    we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        **data
    )
    db.session.add(we)
    db.session.commit()
    return jsonify(workout_exercise_schema.dump(we)), 201
 
 
if __name__ == "__main__":
    app.run(port=5555, debug=True)
 