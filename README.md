# unit-v-assignment
# Student Record Manager (PyQt6) - Unit V Assignment

Desktop GUI to add, edit, delete, search, filter and export student records with per-course marks.
Data is stored in SQLite (`modern_students.db`, created automatically with 5 sample students).

**Name:** Tashi Lhamo  **Roll No:** 27  **Programme:** B.Ed IT (D)  **Module:** PRG304

## Requirements
- Python 3.10 or newer
- PyQt6 (see `requirements.txt`)

## Install and run
```bash
python -m venv venv
# Windows:  venv\Scripts\activate      macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Run the tests (no GUI needed)
```bash
cd PartA/test
PYTHONPATH=../.. python -m unittest test_logic -v     # Windows (PowerShell): $env:PYTHONPATH="../.."
```

## Project structure
| File | Role |
|---|---|
| `main.py` | UI layer: PyQt6 window, layouts, signals/slots, dialogs, stylesheet |
| `logic.py` | Validation, grading, statistics, filtering, CSV export |
| `database.py` | SQLite data layer |
| `modern_students.db` | Database with sample data |
| `PartA/hello_tkinter.py`, `hello_pyqt.py`, `hello_kv.py` | Hello-world programs (Kivy one needs `pip install kivy`) |
| `PartA/test/test_logic.py` | 26 unit tests for the logic and data layers |
