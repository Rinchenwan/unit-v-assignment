"""Data layer: all SQLite access lives here (no GUI code).

Tables
------
students         -> personal details of each student
student_courses  -> one row per (student, course) with that course's marks
"""
import os
import sqlite3

# Built relative to this file, so it works on any machine.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "modern_students.db")

SAMPLE_STUDENTS = [
    {
        "roll_no": "CS-001", "name": "Tashi Dorji", "age": 19,
        "gender": "Male", "scholarship": 1, "remarks": "Top of the class",
        "courses": {
            "Information Technology": 82,
            "Mathematics": 76,
            "English": 68,
        },
    },
    {
        "roll_no": "CS-002", "name": "Pema Wangmo", "age": 20,
        "gender": "Female", "scholarship": 0, "remarks": "",
        "courses": {
            "Information Technology": 74,
            "Dzongkha": 88,
            "Science": 61,
        },
    },
    {
        "roll_no": "CS-003", "name": "Karma Choden", "age": 19,
        "gender": "Female", "scholarship": 1,
        "remarks": "Excellent in algebra",
        "courses": {"Mathematics": 91, "Science": 85},
    },
    {
        "roll_no": "CS-004", "name": "Sonam Tenzin", "age": 21,
        "gender": "Male", "scholarship": 0, "remarks": "Needs extra support",
        "courses": {"Dzongkha": 58, "English": 35, "Mathematics": 47},
    },
    {
        "roll_no": "CS-005", "name": "Dechen Yangzom", "age": 20,
        "gender": "Female", "scholarship": 0, "remarks": "",
        "courses": {"English": 66, "Information Technology": 79},
    },
]


class DatabaseError(Exception):
    """Raised for any database problem."""


class DuplicateRollError(DatabaseError):
    """Raised when a roll number already exists."""


class StudentDB:
    """Reads and writes students. A student is a dictionary:

    {"roll_no", "name", "age", "gender", "scholarship", "remarks",
     "courses": {"Mathematics": 75, "English": 62, ...}}
    """

    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._prepare()

    # -------------------------------------------------
    # Setting up / upgrading the database file
    # -------------------------------------------------

    def _columns(self, table):
        rows = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [row["name"] for row in rows]

    def _prepare(self):
        columns = self._columns("students")

        if not columns:
            # Brand-new database: create tables and add sample data once.
            self._create_tables()
            self._seed()
        elif "course" in columns or "marks" in columns:
            # Database from an older version (one course per student).
            self._upgrade_old_layout()
        else:
            self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    scholarship INTEGER NOT NULL DEFAULT 0,
                    remarks TEXT DEFAULT ''
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS student_courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    course TEXT NOT NULL,
                    marks INTEGER NOT NULL,
                    UNIQUE (student_id, course),
                    FOREIGN KEY (student_id)
                        REFERENCES students(id) ON DELETE CASCADE
                )
            """)

    def _upgrade_old_layout(self):
        """Move the old single course/marks columns into student_courses."""
        self._create_tables()

        already_moved = self.conn.execute(
            "SELECT COUNT(*) FROM student_courses"
        ).fetchone()[0]

        # Rebuilding a table needs foreign keys switched off.
        self.conn.execute("PRAGMA foreign_keys = OFF")
        try:
            with self.conn:
                if not already_moved:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO student_courses
                            (student_id, course, marks)
                        SELECT id, course, marks FROM students
                        WHERE course IS NOT NULL AND course != ''
                          AND marks IS NOT NULL
                    """)

                self.conn.execute("""
                    CREATE TABLE students_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        roll_no TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        gender TEXT NOT NULL,
                        scholarship INTEGER NOT NULL DEFAULT 0,
                        remarks TEXT DEFAULT ''
                    )
                """)
                self.conn.execute("""
                    INSERT INTO students_new
                        (id, roll_no, name, age, gender, scholarship, remarks)
                    SELECT id, roll_no, name, COALESCE(age, 19),
                           COALESCE(gender, ''), COALESCE(scholarship, 0),
                           COALESCE(remarks, '')
                    FROM students
                """)
                self.conn.execute("DROP TABLE students")
                self.conn.execute(
                    "ALTER TABLE students_new RENAME TO students"
                )
        finally:
            self.conn.execute("PRAGMA foreign_keys = ON")

    def _seed(self):
        for student in SAMPLE_STUDENTS:
            self.add(student)

    # -------------------------------------------------
    # Reading
    # -------------------------------------------------

    def count(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

    def get_all(self):
        """All students, newest first, each with its 'courses' dictionary."""
        students = [
            dict(row) for row in self.conn.execute(
                "SELECT * FROM students ORDER BY id DESC"
            ).fetchall()
        ]

        by_id = {}
        for student in students:
            student["courses"] = {}
            by_id[student["id"]] = student

        rows = self.conn.execute(
            "SELECT student_id, course, marks FROM student_courses "
            "ORDER BY id"
        ).fetchall()

        for row in rows:
            if row["student_id"] in by_id:
                by_id[row["student_id"]]["courses"][row["course"]] = (
                    row["marks"]
                )

        return students

    # -------------------------------------------------
    # Writing
    # -------------------------------------------------

    @staticmethod
    def _translate(error):
        """Turn a raw sqlite3 error into one of our own errors."""
        if isinstance(error, sqlite3.IntegrityError) and (
            "roll_no" in str(error)
        ):
            return DuplicateRollError("This roll number already exists.")
        return DatabaseError(str(error))

    def _save_courses(self, student_id, courses):
        for course, marks in courses.items():
            self.conn.execute(
                "INSERT INTO student_courses (student_id, course, marks) "
                "VALUES (?, ?, ?)",
                (student_id, course, marks),
            )

    def add(self, student):
        try:
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO students "
                    "(roll_no, name, age, gender, scholarship, remarks) "
                    "VALUES (:roll_no, :name, :age, :gender, "
                    ":scholarship, :remarks)",
                    student,
                )
                self._save_courses(cursor.lastrowid, student["courses"])
        except sqlite3.Error as error:
            raise self._translate(error) from error

    def update(self, student_id, student):
        try:
            with self.conn:
                self.conn.execute(
                    "UPDATE students SET roll_no=:roll_no, name=:name, "
                    "age=:age, gender=:gender, scholarship=:scholarship, "
                    "remarks=:remarks WHERE id=:id",
                    {**student, "id": student_id},
                )
                self.conn.execute(
                    "DELETE FROM student_courses WHERE student_id = ?",
                    (student_id,),
                )
                self._save_courses(student_id, student["courses"])
        except sqlite3.Error as error:
            raise self._translate(error) from error

    def delete(self, student_id):
        try:
            with self.conn:
                # The student's course rows go too (ON DELETE CASCADE).
                self.conn.execute(
                    "DELETE FROM students WHERE id = ?", (student_id,)
                )
        except sqlite3.Error as error:
            raise self._translate(error) from error

    def close(self):
        self.conn.close()