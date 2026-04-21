from flask import Flask, request, jsonify, make_response
from marshmallow import ValidationError

from server.extensions import db
from server.models import Workout, Exercise, WorkoutExercise
from server.schemas import (
    exercise_schema, exercises_schema,
    workout_schema, workouts_schema,
    workout_exercise_schema
)


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        import server.models   # ensures models register with SQLAlchemy
        db.create_all()

    # ─────────────────────────────────────────────
    # ALL ROUTES MUST BE INSIDE HERE
    # ─────────────────────────────────────────────

    @app.route("/")
    def home():
        return jsonify({"message": "Workout API is running"}), 200

    @app.route("/exercises", methods=["GET"])
    def get_exercises():
        return jsonify(exercises_schema.dump(Exercise.query.all())), 200

    @app.route("/exercises/<int:id>", methods=["GET"])
    def get_exercise(id):
        return jsonify(exercise_schema.dump(Exercise.query.get_or_404(id))), 200

    @app.route("/exercises", methods=["POST"])
    def create_exercise():
        try:
            data = exercise_schema.load(request.get_json())
            exercise = Exercise(**data)
            db.session.add(exercise)
            db.session.commit()
            return jsonify(exercise_schema.dump(exercise)), 201
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 422
        except ValueError as e:
            return jsonify({"error": str(e)}), 422

    @app.route("/exercises/<int:id>", methods=["DELETE"])
    def delete_exercise(id):
        exercise = Exercise.query.get_or_404(id)
        db.session.delete(exercise)
        db.session.commit()
        return make_response("", 204)

    @app.route("/workouts", methods=["GET"])
    def get_workouts():
        return jsonify(workouts_schema.dump(Workout.query.all())), 200

    @app.route("/workouts/<int:id>", methods=["GET"])
    def get_workout(id):
        return jsonify(workout_schema.dump(Workout.query.get_or_404(id))), 200

    @app.route("/workouts", methods=["POST"])
    def create_workout():
        try:
            data = workout_schema.load(request.get_json())
            workout = Workout(**data)
            db.session.add(workout)
            db.session.commit()
            return jsonify(workout_schema.dump(workout)), 201
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 422
        except ValueError as e:
            return jsonify({"error": str(e)}), 422

    @app.route("/workouts/<int:id>", methods=["DELETE"])
    def delete_workout(id):
        workout = Workout.query.get_or_404(id)
        db.session.delete(workout)
        db.session.commit()
        return make_response("", 204)

    @app.route(
        "/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises",
        methods=["POST"]
    )
    def add_exercise_to_workout(workout_id, exercise_id):
        Workout.query.get_or_404(workout_id)
        Exercise.query.get_or_404(exercise_id)

        try:
            data = workout_exercise_schema.load(request.get_json() or {})
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 422

        we = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            **data
        )
        db.session.add(we)
        db.session.commit()

        return jsonify(workout_exercise_schema.dump(we)), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)