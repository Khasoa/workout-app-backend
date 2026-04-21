from marshmallow import Schema, fields, validates, ValidationError, validate
 
 
# ── ExerciseSchema ──
# Serializes Exercise objects to JSON (dump) and validates POST body (load).
 
class ExerciseSchema(Schema):
    id               = fields.Int(dump_only=True)   # read-only: never accepted as input
    name             = fields.Str(required=True, validate=validate.Length(min=2))  # SCHEMA VALIDATION 1
    category         = fields.Str(required=True)
    # load_default=False: optional in POST body — the model default handles it
    equipment_needed = fields.Bool(load_default=False)
 
    @validates("category")
    def validate_category(self, value):
        # SCHEMA VALIDATION 2: whitelist enforced at the API boundary before the model is touched
        valid = ["strength", "cardio", "flexibility", "balance", "core"]
        if value not in valid:
            raise ValidationError(f"Category must be one of: {valid}")
 
 
# ── WorkoutExerciseSchema ──
# Used for POST /workouts/<wid>/exercises/<eid>/workout_exercises
# and for embedding exercise details in workout GET responses.
#
# workout_id and exercise_id are dump_only because they come from the URL,
# not from the request body — loading them from the body would always fail.
 
class WorkoutExerciseSchema(Schema):
    id               = fields.Int(dump_only=True)
    workout_id       = fields.Int(dump_only=True)   # set by the route from the URL
    exercise_id      = fields.Int(dump_only=True)   # set by the route from the URL
    reps             = fields.Int(load_default=None, validate=validate.Range(min=0))  # SCHEMA VALIDATION 3
    sets             = fields.Int(load_default=None, validate=validate.Range(min=0))  # SCHEMA VALIDATION 4
    duration_seconds = fields.Int(load_default=None, validate=validate.Range(min=0))
    # Nested exercise included in GET responses only
    exercise         = fields.Nested(lambda: ExerciseSchema(), dump_only=True)
 
 
# ── WorkoutSchema ──
 
class WorkoutSchema(Schema):
    id               = fields.Int(dump_only=True)
    # fields.Date enforces ISO format (YYYY-MM-DD) and deserializes to a Python date object
    date             = fields.Date(required=True, format="%Y-%m-%d")
    duration_minutes = fields.Int(required=True, validate=validate.Range(min=1))  # SCHEMA VALIDATION 5
    notes            = fields.Str(load_default=None)
    # Nested workout_exercises included in GET responses; ignored on POST input
    workout_exercises = fields.List(
        fields.Nested(WorkoutExerciseSchema()),
        dump_only=True
    )
 
    @validates("duration_minutes")
    def validate_duration(self, value):
        # SCHEMA VALIDATION 6: mirrors model validation — caught at API layer first
        if value <= 0:
            raise ValidationError("Duration must be greater than 0")
 
 
# ── Schema instances ───
# Import these directly into app.py rather than instantiating there.
 
exercise_schema         = ExerciseSchema()
exercises_schema        = ExerciseSchema(many=True)
workout_schema          = WorkoutSchema()
workouts_schema         = WorkoutSchema(many=True)
workout_exercise_schema = WorkoutExerciseSchema()