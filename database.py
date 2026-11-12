"""Data layer: SQLite persistence for students. No GUI imports."""

import csv
import sqlite3
from pathlib import Path

from logic import SUBJECTS, Student

# Relative to this file, so the project runs from any folder (no hard-coded paths).
DEFAULT_DB = Path(__file__).resolve().parent / "data" / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no      TEXT    NOT NULL UNIQUE,
    name         TEXT    NOT NULL,
    email        TEXT    NOT NULL,
    course       TEXT    NOT NULL,
    semester     INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
    gender       TEXT    NOT NULL,
    scholarship  INTEGER NOT NULL DEFAULT 0,
    math         INTEGER NOT NULL CHECK (math BETWEEN 0 AND 100),
    programming  INTEGER NOT NULL CHECK (programming BETWEEN 0 AND 100),
    english      INTEGER NOT NULL CHECK (english BETWEEN 0 AND 100),
    remarks      TEXT    NOT NULL DEFAULT ''
);
"""

COLUMNS = ("roll_no", "name", "email", "course", "semester", "gender",
           "scholarship", "math", "programming", "english", "remarks")

SAMPLE_STUDENTS = [
    Student("CS-101", "Tashi Dorji", "tashi@example.com", "Computer Science", 3, "Male", True, 88, 92, 79, "Top of class"),
    Student("CS-102", "Pema Lhamo", "pema@example.com", "Computer Science", 3, "Female", False, 72, 81, 85),
    Student("IT-201", "Karma Wangchuk", "karma@example.com", "Information Technology", 5, "Male", False, 55, 61, 48),
    Student("EL-301", "Sonam Choden", "sonam@example.com", "Electronics", 2, "Female", True, 67, 59, 74),
    Student("BS-401", "Dechen Zangmo", "dechen@example.com", "Business Studies", 4, "Female", False, 35, 52, 60, "Resit maths"),
    Student("CE-501", "Jigme Tenzin", "jigme@example.com", "Civil Engineering", 6, "Male", False, 78, 70, 66),
]


class DuplicateRollError(Exception):
    """Raised when a roll number already exists."""


class StudentDB:
    def __init__(self, path=DEFAULT_DB):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(SCHEMA)
        self.conn.commit()

    # ---------- helpers ----------
    @staticmethod
    def _to_student(row: sqlite3.Row) -> Student:
        return Student(
            id=row["id"], roll_no=row["roll_no"], name=row["name"], email=row["email"],
            course=row["course"], semester=row["semester"], gender=row["gender"],
            scholarship=bool(row["scholarship"]), math=row["math"],
            programming=row["programming"], english=row["english"], remarks=row["remarks"],
        )

    @staticmethod
    def _values(s: Student) -> tuple:
        return (s.roll_no, s.name, s.email, s.course, s.semester, s.gender,
                int(s.scholarship), s.math, s.programming, s.english, s.remarks)

    # ---------- CRUD ----------
    def add(self, s: Student) -> int:
        sql = f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})"
        try:
            with self.conn:
                cur = self.conn.execute(sql, self._values(s))
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc):
                raise DuplicateRollError(s.roll_no) from exc
            raise
        return cur.lastrowid

    def update(self, student_id: int, s: Student) -> None:
        sql = f"UPDATE students SET {', '.join(c + '=?' for c in COLUMNS)} WHERE id=?"
        try:
            with self.conn:
                self.conn.execute(sql, self._values(s) + (student_id,))
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc):
                raise DuplicateRollError(s.roll_no) from exc
            raise

    def delete(self, student_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM students WHERE id=?", (student_id,))

    def get(self, student_id: int) -> Student | None:
        row = self.conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        return self._to_student(row) if row else None

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    # ---------- search / filter ----------
    def search(self, text: str = "", course: str = "All", min_pct: float = 0) -> list[Student]:
        """Filter by free text (roll/name/email), course and minimum percentage."""
        clauses, params = [], []
        text = text.strip()
        if text:
            escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            like = f"%{escaped}%"
            clauses.append("(roll_no LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' OR email LIKE ? ESCAPE '\\')")
            params += [like, like, like]
        if course and course != "All":
            clauses.append("course = ?")
            params.append(course)
        if min_pct > 0:
            clauses.append("(math + programming + english) / 3.0 >= ?")
            params.append(min_pct)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(f"SELECT * FROM students {where} ORDER BY roll_no", params).fetchall()
        return [self._to_student(r) for r in rows]

    # ---------- import / export ----------
    def export_csv(self, path, students: list[Student] | None = None) -> int:
        students = self.search() if students is None else students
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Roll No", "Name", "Email", "Course", "Semester", "Gender",
                             "Scholarship", *SUBJECTS, "Total", "Percentage", "Grade", "Remarks"])
            for s in students:
                writer.writerow([s.roll_no, s.name, s.email, s.course, s.semester, s.gender,
                                 "Yes" if s.scholarship else "No", s.math, s.programming,
                                 s.english, s.total, f"{s.percentage:.1f}", s.grade, s.remarks])
        return len(students)

    def seed_if_empty(self) -> None:
        """Insert sample rows the first time the app runs."""
        if self.count() == 0:
            for s in SAMPLE_STUDENTS:
                self.add(s)

    def close(self) -> None:
        self.conn.close()
