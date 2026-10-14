# Hybrid MDB Final

Hybrid-MDB-final is a discussion-message filtering application combining keyword rules and machine learning.

![Django](https://img.shields.io/badge/Django-2563EB?style=flat-square) ![SQLite](https://img.shields.io/badge/SQLite-0F172A?style=flat-square)

## Overview

The data model covers `UserRegister`, `Dataset`, `MDBMessage`, `GlobalKeyword`, `ModelPerformance`, `Review`.

## Implemented workflows

The source defines these handlers:

- **Load Latest Models** — `load_latest_models`
- **Index** — `index`
- **Register** — `register`
- **Login** — `login`
- **Logout** — `logout`
- **Student Dashboard** — `student_dashboard`
- **Teacher Dashboard** — `teacher_dashboard`
- **Teacher Mdb Messages** — `teacher_mdb_messages`
- **Teacher Mdb Messages Export Csv** — `teacher_mdb_messages_export_csv`
- **Update Profile** — `update_profile`
- **Manage Keywords** — `manage_keywords`

## Getting started

### 1. Get the project

```bash
git clone https://github.com/nasirabbas827/Hybrid-MDB-final.git
cd Hybrid-MDB-final
```

### 2. Prepare Python

Create an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows Command Prompt, or `source .venv/bin/activate` on macOS/Linux.

No requirements file is included. The inspected Python imports indicate these dependencies as a starting point:

```bash
python -m pip install Django joblib pandas nltk scikit-learn Pillow
```

Dependency versions are not pinned in this repository.

### 3. Configure and run

Review [`myproject/settings.py`](myproject/settings.py) for database, media, and any email configuration. Use a local copy of the supplied database when available.

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. If you need a Django administration account, run `python manage.py createsuperuser`. Application-specific user roles may be managed separately.

### Model files

Included artifacts: [`trained_models/logistic_regression_1.pkl`](trained_models/logistic_regression_1.pkl), [`trained_models/logistic_regression_2.pkl`](trained_models/logistic_regression_2.pkl), [`trained_models/naive_bayes_1.pkl`](trained_models/naive_bayes_1.pkl), [`trained_models/naive_bayes_2.pkl`](trained_models/naive_bayes_2.pkl), [`trained_models/vectorizer_1.pkl`](trained_models/vectorizer_1.pkl), [`trained_models/vectorizer_2.pkl`](trained_models/vectorizer_2.pkl).

Keep models, preprocessing objects, and label mappings together in the locations expected by the source.

## Repository guide

| Path | Purpose |
| --- | --- |
| [`datasets`](datasets) | Dataset resources |
| [`db.sqlite3`](db.sqlite3) | Included SQLite database |
| [`manage.py`](manage.py) | Django command-line entry point |
| [`myapp`](myapp) | Django application modules |
| [`myproject`](myproject) | Django project configuration |
| [`templates`](templates) | HTML page templates |
| [`trained_models`](trained_models) | Saved model artifacts |

## Development notes

These setup instructions are based on the repository source. The application has not been executed as part of this documentation update; verify dependencies and configuration in your local environment.
