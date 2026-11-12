"""Logic layer: the Student model, grading rules and input validation.

This module has NO GUI imports, so it can be unit-tested without PyQt.
"""

import re
from dataclasses import dataclass

COURSES = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Business Studies",
    "Civil Engineering",
]
GENDERS = ("Male", "Female", "Other")
SUBJECTS = ("Mathematics", "Programming", "English")
PASS_MARK = 40  # minimum score needed in every subject

EMAIL_RE = re.compile(r"^\w[\w.+-]*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
# letters/digits, optionally joined by single '-' or '/' (so "CS-101" is fine, "---" is not)
ROLL_RE = re.compile(r"^[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)*$")
# words made of letters, joined by ONE space, hyphen or apostrophe; '.' only after an initial/word
NAME_RE = re.compile(r"^[A-Za-z]+\.?(?:[ '-][A-Za-z]+\.?)*$")


@dataclass
class Student:
    roll_no: str
    name: str
    email: str
    course: str
    semester: int
    gender: str
    scholarship: bool
    math: int
    programming: int
    english: int
    remarks: str = ""
    id: int | None = None

    @property
    def total(self) -> int:
        return self.math + self.programming + self.english

    @property
    def percentage(self) -> float:
        return self.total / len(SUBJECTS)

    @property
    def grade(self) -> str:
        return grade_for(self.percentage)

    @property
    def passed(self) -> bool:
        return min(self.math, self.programming, self.english) >= PASS_MARK


def grade_for(percentage: float) -> str:
    """Map a percentage to a letter grade."""
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    return "F"


def validate_student(s: Student) -> dict[str, str]:
    """Return {field_name: message}. An empty dict means the student is valid."""
    errors: dict[str, str] = {}

    if not s.roll_no:
        errors["roll_no"] = "Roll number is required."
    elif not 3 <= len(s.roll_no) <= 20 or not ROLL_RE.match(s.roll_no):
        errors["roll_no"] = "Roll number must be 3-20 characters: letters/digits, with single '-' or '/' between parts."

    if not s.name:
        errors["name"] = "Name is required."
    elif (len(s.name) > 60 or not NAME_RE.match(s.name)
          or sum(c.isalpha() for c in s.name) < 4):
        errors["name"] = ("Name needs at least 4 letters; use letters only, with a single "
                          "space, hyphen or apostrophe between words.")

    if not s.email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(s.email):
        errors["email"] = "Email format is invalid (e.g. name@example.com)."

    if not s.course:
        errors["course"] = "Course is required - choose one from the list."
    elif s.course not in COURSES:
        errors["course"] = f"'{s.course}' is not a valid course. Choose one from the list."

    if s.gender not in GENDERS:
        errors["gender"] = "Please choose a gender."

    if not isinstance(s.semester, int) or not 1 <= s.semester <= 8:
        errors["semester"] = "Semester must be between 1 and 8."

    for field, label in (("math", "Mathematics"), ("programming", "Programming"),
                         ("english", "English")):
        value = getattr(s, field)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            errors[field] = f"{label} marks must be a whole number from 0 to 100."

    if len(s.remarks) > 300:
        errors["remarks"] = "Remarks must be at most 300 characters."

    return errors
