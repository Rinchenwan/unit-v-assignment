"""Logic layer: validation, grading, statistics, filtering, CSV export.

No GUI code and no database code lives here, so every function can be
tested on its own (see test_logic.py).
"""
import csv
import re

COURSES = [
    "Information Technology",
    "Mathematics",
    "English",
    "Dzongkha",
    "Science",
]
GENDERS = ["Male", "Female", "Other"]

MIN_AGE, MAX_AGE = 15, 60
PASS_MARK = 40

ALL_COURSES = "All Courses"


# -----------------------------------------------------
# Validation
# -----------------------------------------------------

def validate_student(data):
    """Return a list of friendly error messages (empty list = valid)."""
    errors = []

    roll = data.get("roll_no", "").strip()
    name = data.get("name", "").strip()

    if not roll:
        errors.append("Roll number is required.")
    elif not re.fullmatch(r"[A-Za-z0-9\-/]+", roll):
        errors.append(
            "Roll number may only contain letters, digits, '-' or '/'."
        )

    if not name:
        errors.append("Student name is required.")
    elif len(name) < 3:
        errors.append("Name must contain at least 3 characters.")
    elif not re.fullmatch(r"[A-Za-z .'\-]+", name):
        errors.append("Name may only contain letters and spaces.")

    if not (MIN_AGE <= data.get("age", 0) <= MAX_AGE):
        errors.append(f"Age must be between {MIN_AGE} and {MAX_AGE}.")

    if data.get("gender") not in GENDERS:
        errors.append("Please select gender.")

    courses = data.get("courses", {})

    if not courses:
        errors.append("Select at least one course and enter its marks.")

    for course, marks in courses.items():
        if course not in COURSES:
            errors.append(f"'{course}' is not a valid course.")
        elif not (0 <= marks <= 100):
            errors.append(f"Marks for {course} must be between 0 and 100.")

    return errors


# -----------------------------------------------------
# Grades and statistics
# -----------------------------------------------------

def grade_for(marks):
    """Convert marks to a letter grade."""
    if marks >= 80:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= 60:
        return "C"
    if marks >= PASS_MARK:
        return "D"
    return "F"


def student_average(student):
    """Average of all course marks of one student (0 if none)."""
    marks = list(student["courses"].values())
    return sum(marks) / len(marks) if marks else 0.0


def all_results(students):
    """Every individual course mark of every student, as one list."""
    return [
        marks
        for student in students
        for marks in student["courses"].values()
    ]


def overall_average(students):
    """Average of every course result (0 if there are none)."""
    results = all_results(students)
    return sum(results) / len(results) if results else 0.0


def pass_rate(students):
    """Percentage of course results at or above the pass mark."""
    results = all_results(students)
    if not results:
        return 0.0
    passed = sum(1 for marks in results if marks >= PASS_MARK)
    return passed / len(results) * 100


def course_averages(students):
    """{course: average} counting only students who take that course."""
    averages = {}
    for course in COURSES:
        marks = [
            s["courses"][course] for s in students if course in s["courses"]
        ]
        averages[course] = sum(marks) / len(marks) if marks else 0.0
    return averages


def grade_counts(students):
    """{'A': n, 'B': n, ...} counted over every course result."""
    counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for marks in all_results(students):
        counts[grade_for(marks)] += 1
    return counts


# -----------------------------------------------------
# Searching and exporting
# -----------------------------------------------------

def filter_students(students, text="", course=ALL_COURSES):
    """Students whose name or roll number contains text and who take course."""
    text = text.lower().strip()
    matches = []

    for student in students:
        if text and (
            text not in student["name"].lower()
            and text not in student["roll_no"].lower()
        ):
            continue

        if course != ALL_COURSES and course not in student["courses"]:
            continue

        matches.append(student)

    return matches


def write_students_csv(students, path):
    """Write one row per student per course to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Roll No", "Name", "Age", "Gender",
            "Course", "Marks", "Scholarship", "Remarks",
        ])

        for student in students:
            start = [
                student["roll_no"], student["name"],
                student["age"], student["gender"],
            ]
            end = [student["scholarship"], student["remarks"]]

            if student["courses"]:
                for course, marks in student["courses"].items():
                    writer.writerow(start + [course, marks] + end)
            else:
                writer.writerow(start + ["", ""] + end)