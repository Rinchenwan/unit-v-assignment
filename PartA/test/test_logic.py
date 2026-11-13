"""Automated tests for the logic and data layers.

Run from the project folder with:  python -m unittest test_logic -v
(No GUI is started and your real database is never touched.)
"""
import os
import sqlite3
import tempfile
import unittest

import logic
from database import StudentDB, DuplicateRollError


def make_student(**changes):
    """A valid student dictionary; pass keyword arguments to change it."""
    student = {
        "roll_no": "CS-100",
        "name": "Test Student",
        "age": 20,
        "gender": "Female",
        "scholarship": 0,
        "remarks": "",
        "courses": {"Mathematics": 70, "English": 50},
    }
    student.update(changes)
    return student


class ValidationTests(unittest.TestCase):

    def test_valid_student_has_no_errors(self):
        self.assertEqual(logic.validate_student(make_student()), [])

    def test_empty_roll_number(self):
        errors = logic.validate_student(make_student(roll_no=""))
        self.assertIn("Roll number is required.", errors)

    def test_roll_number_with_bad_characters(self):
        errors = logic.validate_student(make_student(roll_no="CS 001!"))
        self.assertEqual(len(errors), 1)

    def test_empty_name(self):
        errors = logic.validate_student(make_student(name=""))
        self.assertIn("Student name is required.", errors)

    def test_short_name(self):
        errors = logic.validate_student(make_student(name="Al"))
        self.assertIn("Name must contain at least 3 characters.", errors)

    def test_name_with_digits(self):
        errors = logic.validate_student(make_student(name="Tashi123"))
        self.assertEqual(len(errors), 1)

    def test_age_out_of_range(self):
        self.assertTrue(logic.validate_student(make_student(age=10)))
        self.assertTrue(logic.validate_student(make_student(age=80)))

    def test_missing_gender(self):
        errors = logic.validate_student(make_student(gender=""))
        self.assertIn("Please select gender.", errors)

    def test_no_courses_selected(self):
        errors = logic.validate_student(make_student(courses={}))
        self.assertTrue(any("at least one course" in e for e in errors))

    def test_marks_out_of_range(self):
        errors = logic.validate_student(
            make_student(courses={"Mathematics": 150})
        )
        self.assertEqual(len(errors), 1)


class StatisticsTests(unittest.TestCase):

    def setUp(self):
        self.students = [
            make_student(roll_no="A-1", name="Anna Lee",
                         courses={"Mathematics": 90, "English": 30}),
            make_student(roll_no="B-2", name="Ben Ray",
                         courses={"Mathematics": 70}),
        ]

    def test_grade_boundaries(self):
        self.assertEqual(logic.grade_for(80), "A")
        self.assertEqual(logic.grade_for(79), "B")
        self.assertEqual(logic.grade_for(60), "C")
        self.assertEqual(logic.grade_for(40), "D")
        self.assertEqual(logic.grade_for(39), "F")

    def test_student_average(self):
        self.assertEqual(logic.student_average(self.students[0]), 60)

    def test_overall_average_uses_every_course_result(self):
        self.assertAlmostEqual(logic.overall_average(self.students), 190 / 3)

    def test_pass_rate_counts_course_results(self):
        # 90, 70 pass; 30 fails -> 2 of 3
        self.assertAlmostEqual(logic.pass_rate(self.students), 200 / 3)

    def test_course_averages_only_count_enrolled_students(self):
        averages = logic.course_averages(self.students)
        self.assertEqual(averages["Mathematics"], 80)
        self.assertEqual(averages["English"], 30)
        self.assertEqual(averages["Science"], 0)

    def test_grade_counts(self):
        counts = logic.grade_counts(self.students)
        self.assertEqual(counts["A"], 1)
        self.assertEqual(counts["B"], 1)
        self.assertEqual(counts["F"], 1)

    def test_empty_class(self):
        self.assertEqual(logic.overall_average([]), 0)
        self.assertEqual(logic.pass_rate([]), 0)

    def test_filter_by_text_and_course(self):
        self.assertEqual(len(logic.filter_students(self.students, "anna")), 1)
        self.assertEqual(len(logic.filter_students(self.students, "b-2")), 1)
        self.assertEqual(
            len(logic.filter_students(self.students, "", "English")), 1
        )
        self.assertEqual(len(logic.filter_students(self.students)), 2)


class DatabaseTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "test.db")
        self.db = StudentDB(self.path)

    def tearDown(self):
        self.db.close()
        self.folder.cleanup()

    def test_new_database_gets_sample_data(self):
        self.assertGreater(self.db.count(), 0)

    def test_add_and_read_back_course_marks(self):
        self.db.add(make_student())
        saved = [s for s in self.db.get_all() if s["roll_no"] == "CS-100"][0]
        self.assertEqual(saved["courses"], {"Mathematics": 70, "English": 50})

    def test_duplicate_roll_number_is_rejected(self):
        self.db.add(make_student())
        with self.assertRaises(DuplicateRollError):
            self.db.add(make_student(name="Someone Else"))

    def test_update_replaces_courses(self):
        self.db.add(make_student())
        saved = [s for s in self.db.get_all() if s["roll_no"] == "CS-100"][0]
        self.db.update(saved["id"], make_student(courses={"Science": 99}))
        again = [s for s in self.db.get_all() if s["roll_no"] == "CS-100"][0]
        self.assertEqual(again["courses"], {"Science": 99})

    def test_delete_removes_student_and_courses(self):
        self.db.add(make_student())
        saved = [s for s in self.db.get_all() if s["roll_no"] == "CS-100"][0]
        before = self.db.count()
        self.db.delete(saved["id"])
        self.assertEqual(self.db.count(), before - 1)
        left = self.db.conn.execute(
            "SELECT COUNT(*) FROM student_courses WHERE student_id = ?",
            (saved["id"],),
        ).fetchone()[0]
        self.assertEqual(left, 0)

    def test_data_survives_reopening(self):
        self.db.add(make_student())
        self.db.close()
        self.db = StudentDB(self.path)
        rolls = [s["roll_no"] for s in self.db.get_all()]
        self.assertIn("CS-100", rolls)

    def test_deleting_everything_does_not_bring_back_samples(self):
        for student in self.db.get_all():
            self.db.delete(student["id"])
        self.db.close()
        self.db = StudentDB(self.path)
        self.assertEqual(self.db.count(), 0)


class OldDatabaseUpgradeTests(unittest.TestCase):
    """A database made by the older one-course-per-student version."""

    def test_old_single_course_database_is_upgraded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "old.db")

            old = sqlite3.connect(path)
            old.execute("""
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    course TEXT NOT NULL,
                    marks INTEGER NOT NULL,
                    scholarship INTEGER NOT NULL DEFAULT 0,
                    remarks TEXT DEFAULT ''
                )
            """)
            old.execute(
                "INSERT INTO students (roll_no, name, age, gender, course, "
                "marks, scholarship, remarks) VALUES "
                "('OLD-1', 'Old Student', 20, 'Male', 'Dzongkha', 77, 1, '')"
            )
            old.commit()
            old.close()

            db = StudentDB(path)
            students = db.get_all()
            self.assertEqual(len(students), 1)
            self.assertEqual(students[0]["courses"], {"Dzongkha": 77})

            # New students can now be added (the old NOT NULL columns are gone).
            db.add(make_student())
            self.assertEqual(db.count(), 2)
            db.close()


if __name__ == "__main__":
    unittest.main()