# Workout API Backend

## Project Description

Workout API Backend is a Flask REST API designed for personal trainers to manage workouts and reusable exercises. Trainers can create workouts, create exercises, attach exercises to workouts, and track sets, reps, or duration.

The project demonstrates Flask backend development using SQLAlchemy ORM, Marshmallow serialization, model validations, schema validations, relational database design, and RESTful routing.

---

## Technologies Used

Python 3.8.13
Flask 2.2.2
Flask-SQLAlchemy 3.0.3
Flask-Migrate 3.1.0
Marshmallow 3.20.1
SQLite
Pipenv

---

## Installation

Clone repository:

```bash
git clone <your-repo-url>
cd workout-app-backend
```

Install dependencies:

```bash
pipenv install
pipenv shell
```

---

## Database Setup

```bash
export FLASK_APP=server/app.py
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

---

## Seed Database

```bash
python server/seed.py
```

---

## Run Application

```bash
python server/app.py
```

Server runs on:

```text
http://127.0.0.1:5555
```

---

## API Endpoints

### Workouts

GET `/workouts` — List all workouts
GET `/workouts/<id>` — Get one workout
POST `/workouts` — Create workout
DELETE `/workouts/<id>` — Delete workout

### Exercises

GET `/exercises` — List all exercises
GET `/exercises/<id>` — Get one exercise
POST `/exercises` — Create exercise
DELETE `/exercises/<id>` — Delete exercise

### Workout Exercises

POST `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` — Add exercise to workout

---

## Testing

cd server && python -m pytest ../tests/test_basic.py -v

All endpoints were tested using cURL commands in the terminal.

### Example Tests

Get all workouts:

```bash
curl http://127.0.0.1:5555/workouts
```

Create workout:

```bash
curl -X POST http://127.0.0.1:5555/workouts \
-H "Content-Type: application/json" \
-d '{"date":"2026-04-25","duration_minutes":50,"notes":"Cardio Day"}'
```

Create exercise:

```bash
curl -X POST http://127.0.0.1:5555/exercises \
-H "Content-Type: application/json" \
-d '{"name":"Burpee","category":"Full Body","equipment_needed":false}'
```

Validation test:

```bash
curl -X POST http://127.0.0.1:5555/workouts \
-H "Content-Type: application/json" \
-d '{"date":"2026-04-25","duration_minutes":-10}'
```

Verified outcomes:

* Successful GET requests returned JSON data
* Successful POST requests created new records
* DELETE requests removed records
* Invalid requests returned 400 errors
* Join table endpoint successfully linked workouts and exercises

---

## Author

Lydia Khasoa
