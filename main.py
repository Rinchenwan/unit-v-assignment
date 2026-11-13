import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
    QRadioButton, QButtonGroup, QTextEdit, QCheckBox,
    QStackedWidget, QFrame, QScrollArea, QMessageBox,
    QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)


from database import StudentDB, DuplicateRollError, DatabaseError
from logic import (
    COURSES, GENDERS, PASS_MARK,
    validate_student, student_average, overall_average, pass_rate,
    course_averages, grade_counts, filter_students, write_students_csv,
)


# =====================================================
# APPLICATION SETTINGS
# =====================================================

# Shown in the window title and the About dialog (needed for screenshots)
STUDENT_NAME = "Tashi Lhamo"
ROLL_NO = "27"
PROGRAMME = "B.Ed IT (D)"


def short_course(name):
    """Short label for a course, used in compact tables."""
    abbreviations = {
        "Information Technology": "IT",
        "Mathematics": "Maths",
    }
    return abbreviations.get(name, name)


STYLE = """
QMainWindow {
    background: #F4F6FB;
}

QWidget {
    font-family: Segoe UI;
    font-size: 13px;
    color: #27334A;
}

QFrame#sidebar {
    background: #17243B;
    border: none;
}

QLabel#brand {
    color: white;
    font-size: 21px;
    font-weight: bold;
}

QLabel#sideTitle {
    color: #8C9AB2;
    font-size: 11px;
    font-weight: bold;
}

QPushButton#nav {
    background: transparent;
    color: #C5CEE0;
    text-align: left;
    padding: 13px;
    border: none;
    border-radius: 7px;
}

QPushButton#nav:hover {
    background: #293A59;
    color: white;
}

QPushButton#navActive {
    background: #4057C8;
    color: white;
    text-align: left;
    padding: 13px;
    border: none;
    border-radius: 7px;
    font-weight: bold;
}

QLabel#pageTitle {
    font-size: 25px;
    font-weight: bold;
    color: #17243B;
}

QLabel#muted {
    color: #8791A5;
}

QFrame#card {
    background: white;
    border: 1px solid #E7EAF1;
    border-radius: 12px;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background: white;
    border: 1px solid #DCE1EB;
    border-radius: 6px;
    padding: 8px;
}

QSpinBox:disabled {
    background: #F1F3F8;
    color: #A4ACBD;
}

QPushButton {
    background: #4057C8;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 9px 15px;
    font-weight: bold;
}

QPushButton:hover {
    background: #3045AC;
}

QPushButton#green {
    background: #159B75;
}

QPushButton#red {
    background: #D94B59;
}

QPushButton#grey {
    background: #E9EDF5;
    color: #34415A;
}

QTableWidget {
    background: white;
    alternate-background-color: #F7F8FC;
    border: 1px solid #E7EAF1;
    gridline-color: #E9ECF2;
    selection-background-color: #E0E7FF;
    selection-color: #26365C;
}

QHeaderView::section {
    background: #F0F2F8;
    color: #59647A;
    padding: 10px;
    border: none;
    font-weight: bold;
}

QProgressBar {
    background: #E9EDF4;
    border: none;
    border-radius: 5px;
    text-align: center;
    min-height: 12px;
}

QProgressBar::chunk {
    background: #4057C8;
    border-radius: 5px;
}
"""


# =====================================================
# REUSABLE WIDGETS
# =====================================================

def make_card(title, value, subtitle):

    card = QFrame()
    card.setObjectName("card")

    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)

    name = QLabel(title)
    name.setObjectName("muted")

    number = QLabel(str(value))
    number.setStyleSheet(
        "font-size:28px; font-weight:bold; color:#263A68;"
    )

    detail = QLabel(subtitle)
    detail.setObjectName("muted")

    layout.addWidget(name)
    layout.addWidget(number)
    layout.addWidget(detail)

    return card, number


class BarChart(QWidget):

    def __init__(self):
        super().__init__()
        self.values = {}
        self.setMinimumHeight(230)

    def set_values(self, values):
        self.values = values
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        top = 30
        bottom = height - 45
        plot_height = max(10, bottom - top)

        painter.setPen(QPen(QColor("#E5E9F1"), 1))

        for i in range(5):
            y = top + i * plot_height // 4
            painter.drawLine(20, y, width - 15, y)

        if not self.values:
            painter.setPen(QColor("#8791A5"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No academic data available"
            )
            return

        items = list(self.values.items())
        count = len(items)

        gap = 18
        available = width - 55
        bar_width = max(
            20, (available - gap * (count - 1)) // count
        )

        for index, (name, value) in enumerate(items):

            x = 30 + index * (bar_width + gap)
            bar_height = int(
                max(0, min(100, value)) / 100 * plot_height
            )
            y = bottom - bar_height

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#4057C8"))

            painter.drawRoundedRect(
                x, y, bar_width, bar_height, 5, 5
            )

            painter.setPen(QColor("#35415A"))
            painter.drawText(
                x - 5, y - 24, bar_width + 10, 20,
                Qt.AlignmentFlag.AlignCenter,
                f"{value:.0f}%"
            )

            painter.setPen(QColor("#68738A"))
            painter.drawText(
                x - 10, height - 27, bar_width + 20, 22,
                Qt.AlignmentFlag.AlignCenter,
                short_course(name)[:9]
            )


# =====================================================
# STUDENT REGISTRATION DIALOG
# =====================================================

class StudentDialog(QDialog):

    def __init__(self, parent=None, student=None):
        super().__init__(parent)

        self.student = student

        self.setWindowTitle(
            "Edit Student" if student else "Register Student"
        )
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)

        title = QLabel(
            "Update Student Profile" if student
            else "New Student Registration"
        )

        title.setStyleSheet(
            "font-size:21px; font-weight:bold; color:#263A68;"
        )

        layout.addWidget(title)

        form = QFormLayout()

        self.roll = QLineEdit()
        self.roll.setPlaceholderText("e.g. CS-001")

        self.name = QLineEdit()
        self.name.setPlaceholderText("Student full name")

        self.age = QSpinBox()
        self.age.setRange(15, 60)
        self.age.setValue(19)

        self.gender_group = QButtonGroup(self)
        gender_layout = QHBoxLayout()
        self.gender_buttons = {}

        for gender in GENDERS:
            button = QRadioButton(gender)
            self.gender_group.addButton(button)
            self.gender_buttons[gender] = button
            gender_layout.addWidget(button)

        self.scholarship = QCheckBox(
            "Receives scholarship"
        )

        self.remarks = QTextEdit()
        self.remarks.setMaximumHeight(70)

        form.addRow("Roll Number:", self.roll)
        form.addRow("Student Name:", self.name)
        form.addRow("Age:", self.age)
        form.addRow("Gender:", gender_layout)
        form.addRow("", self.scholarship)
        form.addRow("Remarks:", self.remarks)

        layout.addLayout(form)

        # ---- Courses: tick a course, then enter its own marks ----

        courses_title = QLabel("Courses and Marks")
        courses_title.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#263A68;"
        )
        courses_hint = QLabel(
            "Tick each course the student takes and enter the "
            "marks for that course."
        )
        courses_hint.setObjectName("muted")

        layout.addWidget(courses_title)
        layout.addWidget(courses_hint)

        courses_box = QFrame()
        courses_box.setObjectName("card")
        courses_grid = QGridLayout(courses_box)
        courses_grid.setColumnStretch(0, 1)

        self.course_checks = {}
        self.course_marks = {}

        for row, course in enumerate(COURSES):

            check = QCheckBox(course)

            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setSuffix(" / 100")
            spin.setEnabled(False)

            check.toggled.connect(spin.setEnabled)

            self.course_checks[course] = check
            self.course_marks[course] = spin

            courses_grid.addWidget(check, row, 0)
            courses_grid.addWidget(spin, row, 1)

        layout.addWidget(courses_box)

        buttons = QHBoxLayout()

        cancel = QPushButton("Cancel")
        cancel.setObjectName("grey")

        save = QPushButton(
            "Update Profile" if student else "Save Student"
        )
        save.setObjectName("green")

        buttons.addWidget(cancel)
        buttons.addWidget(save)

        layout.addLayout(buttons)

        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.validate_and_accept)

        if student:
            self.fill_existing()

    def fill_existing(self):

        s = self.student

        self.roll.setText(s["roll_no"])
        self.name.setText(s["name"])
        self.age.setValue(s["age"] or 19)

        if s["gender"] in self.gender_buttons:
            self.gender_buttons[s["gender"]].setChecked(True)

        self.scholarship.setChecked(bool(s["scholarship"]))
        self.remarks.setPlainText(s["remarks"] or "")

        for course, marks in s["courses"].items():
            if course in self.course_checks:
                self.course_checks[course].setChecked(True)
                self.course_marks[course].setValue(marks)

    def get_data(self):
        """Return the form contents as one student dictionary."""

        gender = self.gender_group.checkedButton()

        return {
            "roll_no": self.roll.text().strip(),
            "name": self.name.text().strip(),
            "age": self.age.value(),
            "gender": gender.text() if gender else "",
            "scholarship": int(self.scholarship.isChecked()),
            "remarks": self.remarks.toPlainText().strip(),
            "courses": {
                course: self.course_marks[course].value()
                for course in COURSES
                if self.course_checks[course].isChecked()
            },
        }

    def validate_and_accept(self):

        errors = validate_student(self.get_data())

        if errors:
            QMessageBox.warning(
                self,
                "Check Information",
                "\n".join(errors)
            )
            return

        self.accept()


# =====================================================
# MAIN APPLICATION
# =====================================================

class StudentApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.db = StudentDB()
        self.students = []

        self.setWindowTitle(
            f"Student Management Dashboard - {STUDENT_NAME} ({ROLL_NO})"
        )
        self.resize(1320, 800)
        self.setMinimumSize(1050, 650)
        self.setStyleSheet(STYLE)

        self.build_window()
        self.build_menu()
        self.refresh()

    # -------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------

    def build_window(self):

        central = QWidget()
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Sidebar

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(225)

        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(15, 25, 15, 20)

        brand = QLabel("STUDENT\nPORTAL")
        brand.setObjectName("brand")
        side.addWidget(brand)

        side.addSpacing(35)

        section = QLabel("MAIN MENU")
        section.setObjectName("sideTitle")
        side.addWidget(section)

        self.stack = QStackedWidget()

        self.pages = [
            self.dashboard_page(),
            self.directory_page(),
            self.analytics_page()
        ]

        self.nav_buttons = []

        names = [
            "▦   Dashboard",
            "◉   Students",
            "▥   Analytics"
        ]

        for index, name in enumerate(names):

            button = QPushButton(name)
            button.setObjectName("nav")

            button.clicked.connect(
                lambda checked=False, i=index: self.change_page(i)
            )

            self.nav_buttons.append(button)
            side.addWidget(button)

        side.addStretch()

        footer = QLabel("Student Management\nSystem  |  Version 1.1")
        footer.setStyleSheet(
            "color:#8492AA; font-size:11px;"
        )
        side.addWidget(footer)

        # Workspace

        workspace = QVBoxLayout()

        self.topbar = QFrame()
        self.topbar.setObjectName("card")
        self.topbar.setMaximumHeight(65)

        top_layout = QHBoxLayout(self.topbar)

        self.page_heading = QLabel("Dashboard")
        self.page_heading.setStyleSheet(
            "font-size:17px; font-weight:bold;"
        )

        top_layout.addWidget(self.page_heading)
        top_layout.addStretch()

        export_button = QPushButton("Export CSV")
        export_button.setObjectName("grey")
        export_button.clicked.connect(self.export_csv)

        add_button = QPushButton("+ Add Student")
        add_button.clicked.connect(self.add_student)

        top_layout.addWidget(export_button)
        top_layout.addWidget(add_button)

        workspace.addWidget(self.topbar)

        for page in self.pages:
            self.stack.addWidget(page)

        workspace.addWidget(self.stack, 1)

        workspace_widget = QWidget()
        workspace_widget.setLayout(workspace)

        workspace_widget.setContentsMargins(15, 10, 15, 12)

        main.addWidget(self.sidebar)
        main.addWidget(workspace_widget, 1)

        self.change_page(0)

    def build_menu(self):

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        export_action = QAction("Export CSV...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        students_menu = menu_bar.addMenu("&Students")

        add_action = QAction("Add Student", self)
        add_action.setShortcut(QKeySequence("Ctrl+N"))
        add_action.triggered.connect(self.add_student)
        students_menu.addAction(add_action)

        view_menu = menu_bar.addMenu("&View")

        for index, name in enumerate(
            ["Dashboard", "Students", "Analytics"]
        ):
            action = QAction(name, self)
            action.triggered.connect(
                lambda checked=False, i=index: self.change_page(i)
            )
            view_menu.addAction(action)

        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):

        QMessageBox.about(
            self,
            "About Student Management System",
            f"<h3>Student Management System</h3>"
            f"<p>Built with PyQt6 and SQLite.</p>"
            f"<p><b>Name:</b> {STUDENT_NAME}<br>"
            f"<b>Roll No:</b> {ROLL_NO}<br>"
            f"<b>Programme:</b> {PROGRAMME}</p>"
        )

    def change_page(self, index):

        self.stack.setCurrentIndex(index)

        titles = ["Dashboard", "Student Directory", "Analytics"]

        self.page_heading.setText(titles[index])

        for i, button in enumerate(self.nav_buttons):
            button.setObjectName(
                "navActive" if i == index else "nav"
            )
            button.style().unpolish(button)
            button.style().polish(button)

    # -------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------

    def dashboard_page(self):

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        welcome = QLabel("Welcome Back!")
        welcome.setObjectName("pageTitle")

        description = QLabel(
            "Here is an overview of your student information."
        )
        description.setObjectName("muted")

        layout.addWidget(welcome)
        layout.addWidget(description)

        cards = QGridLayout()

        card1, self.total_number = make_card(
            "TOTAL STUDENTS", 0, "Registered students"
        )

        card2, self.average_number = make_card(
            "CLASS AVERAGE", "0%", "Average of all course marks"
        )

        card3, self.scholarship_number = make_card(
            "SCHOLARSHIPS", 0, "Scholarship recipients"
        )

        card4, self.pass_number = make_card(
            "PASS RATE", "0%",
            f"Course results of {PASS_MARK} or above"
        )

        cards.addWidget(card1, 0, 0)
        cards.addWidget(card2, 0, 1)
        cards.addWidget(card3, 0, 2)
        cards.addWidget(card4, 0, 3)

        layout.addLayout(cards)

        # Chart and activity

        lower = QVBoxLayout()

        chart_card = QFrame()
        chart_card.setObjectName("card")

        chart_layout = QVBoxLayout(chart_card)

        chart_title = QLabel("Course Performance")
        chart_title.setStyleSheet(
            "font-size:16px; font-weight:bold;"
        )

        chart_layout.addWidget(chart_title)

        self.dashboard_chart = BarChart()
        self.dashboard_chart.setMinimumHeight(270)
        chart_layout.addWidget(self.dashboard_chart)

        lower.addWidget(chart_card, 1)

        activity_card = QFrame()
        activity_card.setObjectName("card")

        activity_layout = QVBoxLayout(activity_card)

        activity_title = QLabel("All Students - Marks in Every Subject")
        activity_title.setStyleSheet(
            "font-size:16px; font-weight:bold;"
        )

        activity_hint = QLabel(
            f"Red marks are below the pass mark ({PASS_MARK}). "
            "A dash (-) means the student does not take that subject."
        )
        activity_hint.setObjectName("muted")

        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(activity_hint)

        headers = (
            ["Roll No", "Name"]
            + [short_course(c) for c in COURSES]
            + ["Average"]
        )

        self.marks_table = QTableWidget(0, len(headers))
        self.marks_table.setHorizontalHeaderLabels(headers)

        header = self.marks_table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )

        self.marks_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.marks_table.setAlternatingRowColors(True)
        self.marks_table.verticalHeader().setVisible(False)
        self.marks_table.setMinimumHeight(340)

        activity_layout.addWidget(self.marks_table)

        lower.addWidget(activity_card)

        layout.addLayout(lower)

        # The whole dashboard scrolls, so nothing gets squeezed

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        scroll.setWidget(content)

        return scroll

    # -------------------------------------------------
    # STUDENT DIRECTORY
    # -------------------------------------------------

    def directory_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Student Profiles")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Browse, search, edit and manage registered students."
        )
        subtitle.setObjectName("muted")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        filters = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search student name or roll number..."
        )

        self.course_filter = QComboBox()
        self.course_filter.addItem("All Courses")
        self.course_filter.addItems(COURSES)

        filters.addWidget(self.search_box, 2)
        filters.addWidget(self.course_filter, 1)

        layout.addLayout(filters)

        self.profile_scroll = QScrollArea()
        self.profile_scroll.setWidgetResizable(True)
        self.profile_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.profile_container = QWidget()
        self.profile_grid = QGridLayout(self.profile_container)
        self.profile_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.profile_grid.setSpacing(14)

        self.profile_scroll.setWidget(self.profile_container)

        layout.addWidget(self.profile_scroll, 1)

        self.search_box.textChanged.connect(self.display_profiles)
        self.course_filter.currentTextChanged.connect(
            self.display_profiles
        )

        return page

    def display_profiles(self):

        while self.profile_grid.count():

            item = self.profile_grid.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

        search = self.search_box.text().lower().strip()
        course = self.course_filter.currentText()

        filtered = filter_students(self.students, search, course)

        if not filtered:

            empty = QLabel("No matching student profiles found.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                "font-size:16px; color:#8791A5; padding:40px;"
            )

            self.profile_grid.addWidget(empty, 0, 0)
            return

        for index, student in enumerate(filtered):

            row = index // 3
            column = index % 3

            self.profile_grid.addWidget(
                self.create_profile_card(student),
                row, column
            )

    def create_profile_card(self, student):

        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(220)

        layout = QVBoxLayout(card)

        top = QHBoxLayout()

        avatar = QLabel(
            student["name"][:1].upper()
        )

        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(43, 43)

        avatar.setStyleSheet("""
            background:#E3E8FF;
            color:#4057C8;
            font-size:20px;
            font-weight:bold;
            border-radius:21px;
        """)

        identity = QVBoxLayout()

        name = QLabel(student["name"])
        name.setStyleSheet(
            "font-size:16px; font-weight:bold;"
        )

        roll = QLabel(student["roll_no"])
        roll.setObjectName("muted")

        identity.addWidget(name)
        identity.addWidget(roll)

        top.addWidget(avatar)
        top.addLayout(identity)
        top.addStretch()

        layout.addLayout(top)

        layout.addWidget(QLabel("Age: " + str(student["age"])))
        layout.addWidget(
            QLabel("Scholarship: " +
                   ("Yes" if student["scholarship"] else "No"))
        )

        average = QLabel(
            f"Overall Average: {student_average(student):.1f}%"
        )
        average.setStyleSheet(
            "font-weight:bold; color:#4057C8;"
        )
        layout.addWidget(average)

        # One line + progress bar for EACH course with its own marks
        if student["courses"]:
            for course, marks in student["courses"].items():

                course_row = QHBoxLayout()

                course_label = QLabel(course)
                course_label.setMinimumWidth(130)

                mark_label = QLabel(f"{marks}%")
                mark_label.setMinimumWidth(40)
                mark_label.setAlignment(
                    Qt.AlignmentFlag.AlignRight
                )
                mark_label.setStyleSheet("font-weight:bold;")

                course_row.addWidget(course_label)
                course_row.addStretch()
                course_row.addWidget(mark_label)

                layout.addLayout(course_row)

                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setValue(marks)
                progress.setFormat("")
                progress.setMaximumHeight(8)

                layout.addWidget(progress)
        else:
            none_label = QLabel("No courses registered.")
            none_label.setObjectName("muted")
            layout.addWidget(none_label)

        layout.addStretch()

        buttons = QHBoxLayout()

        edit = QPushButton("Edit")
        edit.setObjectName("grey")

        delete = QPushButton("Delete")
        delete.setObjectName("red")

        edit.clicked.connect(
            lambda checked=False, s=student: self.edit_student(s)
        )

        delete.clicked.connect(
            lambda checked=False, s=student: self.delete_student(s)
        )

        buttons.addWidget(edit)
        buttons.addWidget(delete)

        layout.addLayout(buttons)

        return card

    # -------------------------------------------------
    # ANALYTICS
    # -------------------------------------------------

    def analytics_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Academic Analytics")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Understand student results and course performance."
        )
        subtitle.setObjectName("muted")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        chart_card = QFrame()
        chart_card.setObjectName("card")

        chart_layout = QVBoxLayout(chart_card)

        chart_title = QLabel("Average Marks by Course")
        chart_title.setStyleSheet(
            "font-size:17px; font-weight:bold;"
        )

        chart_layout.addWidget(chart_title)

        self.analytics_chart = BarChart()
        chart_layout.addWidget(self.analytics_chart)

        layout.addWidget(chart_card)

        # Grade distribution (counts every course result)

        grade_card = QFrame()
        grade_card.setObjectName("card")

        grade_layout = QVBoxLayout(grade_card)

        grade_title = QLabel("Grade Distribution (all course results)")
        grade_title.setStyleSheet(
            "font-size:17px; font-weight:bold;"
        )

        grade_layout.addWidget(grade_title)

        self.grade_labels = {}

        for grade in ["A", "B", "C", "D", "F"]:

            row = QHBoxLayout()

            label = QLabel("Grade " + grade)
            label.setMinimumWidth(80)

            bar = QProgressBar()
            bar.setRange(0, 100)

            number = QLabel("0 results")
            number.setMinimumWidth(95)

            self.grade_labels[grade] = (bar, number)

            row.addWidget(label)
            row.addWidget(bar, 1)
            row.addWidget(number)

            grade_layout.addLayout(row)

        layout.addWidget(grade_card)
        layout.addStretch()

        return page

    # -------------------------------------------------
    # ADD STUDENT
    # -------------------------------------------------

    def add_student(self):

        dialog = StudentDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:

            self.db.add(dialog.get_data())

            QMessageBox.information(
                self,
                "Success",
                "Student registered successfully."
            )

            self.refresh()

        except DuplicateRollError as error:

            QMessageBox.warning(
                self,
                "Duplicate Roll Number",
                str(error)
            )

        except DatabaseError as error:

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

    # -------------------------------------------------
    # EDIT STUDENT
    # -------------------------------------------------

    def edit_student(self, student):

        dialog = StudentDialog(self, student)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:

            self.db.update(student["id"], dialog.get_data())

            QMessageBox.information(
                self,
                "Updated",
                "Student profile updated successfully."
            )

            self.refresh()

        except DuplicateRollError as error:

            QMessageBox.warning(
                self,
                "Duplicate Roll Number",
                str(error)
            )

        except DatabaseError as error:

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

    # -------------------------------------------------
    # DELETE STUDENT
    # -------------------------------------------------

    def delete_student(self, student):

        answer = QMessageBox.question(
            self,
            "Delete Student",
            f"Delete the record of {student['name']}?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            self.db.delete(student["id"])
            self.refresh()

        except DatabaseError as error:

            QMessageBox.critical(
                self,
                "Database Error",
                str(error)
            )

    # -------------------------------------------------
    # TABLE CELL HELPER
    # -------------------------------------------------

    def set_cell(self, row, col, text, center=False,
                 low=False, bold=False):

        item = QTableWidgetItem(text)

        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if low:
            item.setForeground(QColor("#D94B59"))

        if bold or low:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        self.marks_table.setItem(row, col, item)

    # -------------------------------------------------
    # REFRESH DASHBOARD AND ANALYTICS
    # -------------------------------------------------

    def refresh(self):

        self.students = self.db.get_all()

        total = len(self.students)
        average = overall_average(self.students)
        passed = pass_rate(self.students)

        scholarship = sum(
            1 for s in self.students if s["scholarship"]
        )

        self.total_number.setText(str(total))
        self.average_number.setText(f"{average:.1f}%")
        self.scholarship_number.setText(str(scholarship))
        self.pass_number.setText(f"{passed:.1f}%")

        # Dashboard table: every student, one column per subject

        self.marks_table.setRowCount(len(self.students))

        last_col = 2 + len(COURSES)

        for row, student in enumerate(self.students):

            self.set_cell(row, 0, student["roll_no"])
            self.set_cell(row, 1, student["name"])

            for index, course in enumerate(COURSES):

                marks = student["courses"].get(course)

                if marks is None:
                    self.set_cell(row, 2 + index, "-", center=True)
                else:
                    self.set_cell(
                        row, 2 + index, str(marks),
                        center=True, low=marks < PASS_MARK
                    )

            if student["courses"]:
                self.set_cell(
                    row, last_col,
                    f"{student_average(student):.1f}%",
                    center=True, bold=True
                )
            else:
                self.set_cell(row, last_col, "-", center=True)

        # Course averages (only students enrolled in that course)

        course_values = course_averages(self.students)

        self.dashboard_chart.set_values(course_values)
        self.analytics_chart.set_values(course_values)

        # Grade distribution (per course result)

        counts = grade_counts(self.students)
        result_total = sum(counts.values())

        for grade, (bar, number) in self.grade_labels.items():

            percentage = (
                counts[grade] / result_total * 100
                if result_total else 0
            )

            bar.setValue(round(percentage))
            number.setText(f"{counts[grade]} results")

        self.display_profiles()

    # -------------------------------------------------
    # CSV EXPORT (one row per student per course)
    # -------------------------------------------------

    def export_csv(self):

        if not self.students:

            QMessageBox.information(
                self,
                "No Data",
                "There are no student records to export."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Student Records",
            "student_records.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        try:

            write_students_csv(self.students, path)

            QMessageBox.information(
                self,
                "Export Complete",
                "Student records exported successfully."
            )

        except OSError as error:

            QMessageBox.critical(
                self,
                "Export Error",
                str(error)
            )

    # -------------------------------------------------
    # CLOSE APPLICATION
    # -------------------------------------------------

    def closeEvent(self, event):

        self.db.close()
        event.accept()


# =====================================================
# START APPLICATION
# =====================================================

def main():

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = StudentApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()