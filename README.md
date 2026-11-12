# Student Record Manager (PyQt6 + SQLite)

Unit V assignment project: add, edit, search, filter, delete and export student records with marks.

## Requirements
- Python 3.10 or newer
- PyQt6 (installed from `requirements.txt`)

## Install and run

```bash
# 1. create and activate a virtual environment
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. set your identity (shown in the window title and About dialog)
#    edit config.py -> STUDENT_NAME and ROLL_NUMBER

# 4. run
python main.py
```

To pin the exact version you used for your report, run `pip freeze | findstr PyQt6`
(Windows) or `pip freeze | grep PyQt6` (macOS/Linux) and paste the result into `requirements.txt`.

## Run the tests (no GUI needed)

```bash
python -m unittest -v
```

## Project layout

| File | Layer | Purpose |
|------|-------|---------|
| `main.py` | entry | creates `QApplication`, applies stylesheet, opens the window |
| `main_window.py` | UI | widgets, layouts, signals/slots, dialogs |
| `styles.py` | UI | Qt stylesheet (QSS) |
| `logic.py` | logic | `Student` model, grading rules, input validation |
| `database.py` | data | SQLite CRUD, search/filter, CSV export, sample data |
| `config.py` | config | app title, your name and roll number |
| `test_logic.py` | tests | unit tests for logic and data layers |
| `data/students.db` | data | SQLite file with sample students (auto-created if missing) |

## Using the app
- **Add**: fill the form and click *Add*. Required fields are marked `*`.
- **Edit / Delete**: click a row in the table, change the form, then *Update* (or *Delete*, which asks for confirmation).
- **Search**: type in the search box; use the course drop-down and the *Min %* slider to filter.
- **Sort**: click a column header.
- **Export**: *File > Export to CSV* saves the rows currently shown.
- **Reset data**: delete `data/students.db`; sample data is recreated on next launch.
