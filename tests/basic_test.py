"""
 
Tests cover:
  - Model validations (@validates)
  - Schema validations (marshmallow)
  - All API endpoints (status codes + response shape)
"""
 
import sys
import os
import pytest
from datetime import date, timedelta
 
# Make sure the server/ directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
 
from app import app as flask_app
from models import db, Workout, Exercise, WorkoutExercise
 
 
# ── Fixtures ──────────────────────────────────────────────────────────────────
 
@pytest.fixture
def app():
    """Configure Flask for testing: in-memory SQLite, no propagated exceptions."""
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
 
 
@pytest.fixture
def client(app):
    """Test client for making HTTP requests."""
    return app.test_client()
 
 
@pytest.fixture
def sample_data(app):
    """
    Insert one Exercise and one Workout into the test DB.
    Returns them so tests can reference their IDs.
    """
    with app.app_context():
        exercise = Exercise(name="Squat", category="strength", equipment_needed=False)
        workout  = Workout(date=date(2024, 4, 1), duration_minutes=60, notes="Leg day")
        db.session.add_all([exercise, workout])
        db.session.commit()
        # Refresh to get IDs before session closes
        db.session.refresh(exercise)
        db.session.refresh(workout)
        return {"exercise_id": exercise.id, "workout_id": workout.id}
 
 
# ── Model Validation Tests ────────────────────────────────────────────────────
 
class TestModelValidations:
 
    def test_exercise_name_too_short_raises(self, app):
        """@validates('name') should raise ValueError for names under 2 chars."""
        with app.app_context():
            with pytest.raises(ValueError, match="at least 2 characters"):
                Exercise(name="A", category="strength", equipment_needed=False)
 
    def test_exercise_blank_name_raises(self, app):
        """Blank/whitespace-only names should be rejected."""
        with app.app_context():
            with pytest.raises(ValueError):
                Exercise(name="   ", category="strength", equipment_needed=False)
 
    def test_exercise_invalid_category_raises(self, app):
        """@validates('category') should reject categories not in the allowed list."""
        with app.app_context():
            with pytest.raises(ValueError, match="Category must be one of"):
                Exercise(name="Squat", category="legs", equipment_needed=False)
 
    def test_workout_zero_duration_raises(self, app):
        """Duration of 0 should be rejected by @validates('duration_minutes')."""
        with app.app_context():
            with pytest.raises(ValueError, match="greater than 0"):
                Workout(date=date(2024, 4, 1), duration_minutes=0)
 
    def test_workout_negative_duration_raises(self, app):
        """Negative duration should be rejected."""
        with app.app_context():
            with pytest.raises(ValueError):
                Workout(date=date(2024, 4, 1), duration_minutes=-10)
 
    def test_workout_future_date_raises(self, app):
        """Dates in the future should be rejected by @validates('date')."""
        with app.app_context():
            future = date.today() + timedelta(days=7)
            with pytest.raises(ValueError, match="future"):
                Workout(date=future, duration_minutes=30)
 
    def test_valid_exercise_saves(self, app):
        """A properly formed Exercise should save without error."""
        with app.app_context():
            e = Exercise(name="Deadlift", category="strength", equipment_needed=True)
            db.session.add(e)
            db.session.commit()
            assert Exercise.query.count() == 1
 
    def test_valid_workout_saves(self, app):
        """A properly formed Workout should save without error."""
        with app.app_context():
            w = Workout(date=date(2024, 1, 1), duration_minutes=45)
            db.session.add(w)
            db.session.commit()
            assert Workout.query.count() == 1
 
 
# ── Schema Validation Tests ───────────────────────────────────────────────────
 
class TestSchemaValidations:
 
    def test_exercise_schema_rejects_short_name(self):
        """Schema should reject names shorter than 2 characters before hitting the model."""
        from schemas import exercise_schema
        from marshmallow import ValidationError
        with pytest.raises(ValidationError):
            exercise_schema.load({"name": "A", "category": "strength"})
 
    def test_exercise_schema_rejects_invalid_category(self):
        """Schema category @validates should reject non-whitelisted values."""
        from schemas import exercise_schema
        from marshmallow import ValidationError
        with pytest.raises(ValidationError):
            exercise_schema.load({"name": "Squat", "category": "legs"})
 
    def test_workout_schema_rejects_zero_duration(self):
        """Schema should reject duration_minutes <= 0."""
        from schemas import workout_schema
        from marshmallow import ValidationError
        with pytest.raises(ValidationError):
            workout_schema.load({"date": "2024-04-01", "duration_minutes": 0})
 
    def test_workout_schema_requires_date(self):
        """Missing date field should raise ValidationError."""
        from schemas import workout_schema
        from marshmallow import ValidationError
        with pytest.raises(ValidationError):
            workout_schema.load({"duration_minutes": 30})
 
    def test_workout_exercise_schema_rejects_negative_reps(self):
        """Schema should reject negative reps."""
        from schemas import workout_exercise_schema
        from marshmallow import ValidationError
        with pytest.raises(ValidationError):
            workout_exercise_schema.load({"reps": -5})
 
 
# ── Endpoint Tests ────────────────────────────────────────────────────────────
 
class TestExerciseEndpoints:
 
    def test_get_exercises_empty(self, client):
        res = client.get("/exercises")
        assert res.status_code == 200
        assert res.get_json() == []
 
    def test_get_exercises_returns_list(self, client, sample_data):
        res = client.get("/exercises")
        assert res.status_code == 200
        assert len(res.get_json()) == 1
 
    def test_get_single_exercise(self, client, sample_data):
        res = client.get(f"/exercises/{sample_data['exercise_id']}")
        assert res.status_code == 200
        assert res.get_json()["name"] == "Squat"
 
    def test_get_exercise_not_found(self, client):
        res = client.get("/exercises/9999")
        assert res.status_code == 404
 
    def test_create_exercise_success(self, client):
        res = client.post("/exercises", json={
            "name": "Pull Up",
            "category": "strength"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["name"] == "Pull Up"
        assert data["equipment_needed"] is False  # default applied
 
    def test_create_exercise_missing_name(self, client):
        res = client.post("/exercises", json={"category": "strength"})
        assert res.status_code == 422
 
    def test_create_exercise_invalid_category(self, client):
        res = client.post("/exercises", json={"name": "Squat", "category": "legs"})
        assert res.status_code == 422
 
    def test_create_exercise_short_name(self, client):
        res = client.post("/exercises", json={"name": "A", "category": "strength"})
        assert res.status_code == 422
 
    def test_delete_exercise(self, client, sample_data):
        res = client.delete(f"/exercises/{sample_data['exercise_id']}")
        assert res.status_code == 204
 
    def test_delete_exercise_not_found(self, client):
        res = client.delete("/exercises/9999")
        assert res.status_code == 404
 
 
class TestWorkoutEndpoints:
 
    def test_get_workouts_empty(self, client):
        res = client.get("/workouts")
        assert res.status_code == 200
        assert res.get_json() == []
 
    def test_get_workouts_returns_list(self, client, sample_data):
        res = client.get("/workouts")
        assert res.status_code == 200
        assert len(res.get_json()) == 1
 
    def test_get_single_workout(self, client, sample_data):
        res = client.get(f"/workouts/{sample_data['workout_id']}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["duration_minutes"] == 60
        assert "workout_exercises" in data  # stretch goal: nested data present
 
    def test_get_workout_not_found(self, client):
        res = client.get("/workouts/9999")
        assert res.status_code == 404
 
    def test_create_workout_success(self, client):
        res = client.post("/workouts", json={
            "date": "2024-03-01",
            "duration_minutes": 45,
            "notes": "Test session"
        })
        assert res.status_code == 201
        assert res.get_json()["duration_minutes"] == 45
 
    def test_create_workout_missing_date(self, client):
        res = client.post("/workouts", json={"duration_minutes": 45})
        assert res.status_code == 422
 
    def test_create_workout_zero_duration(self, client):
        res = client.post("/workouts", json={"date": "2024-03-01", "duration_minutes": 0})
        assert res.status_code == 422
 
    def test_create_workout_negative_duration(self, client):
        res = client.post("/workouts", json={"date": "2024-03-01", "duration_minutes": -5})
        assert res.status_code == 422
 
    def test_delete_workout(self, client, sample_data):
        res = client.delete(f"/workouts/{sample_data['workout_id']}")
        assert res.status_code == 204
 
    def test_delete_workout_not_found(self, client):
        res = client.delete("/workouts/9999")
        assert res.status_code == 404
 
 
class TestWorkoutExerciseEndpoint:
 
    def test_add_exercise_to_workout_success(self, client, sample_data):
        """Should create a WorkoutExercise link and return 201."""
        res = client.post(
            f"/workouts/{sample_data['workout_id']}"
            f"/exercises/{sample_data['exercise_id']}/workout_exercises",
            json={"sets": 3, "reps": 10}
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["sets"] == 3
        assert data["reps"] == 10
 
    def test_add_exercise_empty_body_allowed(self, client, sample_data):
        """All fields are optional — empty body should succeed."""
        res = client.post(
            f"/workouts/{sample_data['workout_id']}"
            f"/exercises/{sample_data['exercise_id']}/workout_exercises",
            json={}
        )
        assert res.status_code == 201
 
    def test_add_exercise_negative_reps_rejected(self, client, sample_data):
        """Negative reps should return 422."""
        res = client.post(
            f"/workouts/{sample_data['workout_id']}"
            f"/exercises/{sample_data['exercise_id']}/workout_exercises",
            json={"reps": -1}
        )
        assert res.status_code == 422
 
    def test_add_exercise_workout_not_found(self, client, sample_data):
        """Should return 404 if the workout doesn't exist."""
        res = client.post(
            f"/workouts/9999/exercises/{sample_data['exercise_id']}/workout_exercises",
            json={"sets": 3}
        )
        assert res.status_code == 404
 
    def test_add_exercise_exercise_not_found(self, client, sample_data):
        """Should return 404 if the exercise doesn't exist."""
        res = client.post(
            f"/workouts/{sample_data['workout_id']}/exercises/9999/workout_exercises",
            json={"sets": 3}
        )
        assert res.status_code == 404
 
    def test_workout_response_includes_exercise_details(self, client, sample_data):
        """After linking, GET /workouts/<id> should return nested exercise data."""
        client.post(
            f"/workouts/{sample_data['workout_id']}"
            f"/exercises/{sample_data['exercise_id']}/workout_exercises",
            json={"sets": 4, "reps": 12}
        )
        res = client.get(f"/workouts/{sample_data['workout_id']}")
        data = res.get_json()
        assert len(data["workout_exercises"]) == 1
        assert data["workout_exercises"][0]["exercise"]["name"] == "Squat"
        assert data["workout_exercises"][0]["reps"] == 12