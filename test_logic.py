"""Unit tests for the logic + data layers (no GUI needed).

Run:  python -m unittest -v
"""

import csv
import os
import tempfile
import unittest
from dataclasses import replace

from database import DuplicateRollError, StudentDB
from logic import Student, grade_for, validate_student


def make(**overrides) -> Student:
    base = Student("CS-900", "Test Student", "test@example.com", "Computer Science",
                   3, "Male", False, 70, 80, 90)
    return replace(base, **overrides)


class ValidationTests(unittest.TestCase):
    def test_valid_student(self):
        self.assertEqual(validate_student(make()), {})

    def test_empty_name(self):
        self.assertIn("name", validate_student(make(name="")))

    def test_short_name(self):
        self.assertIn("name", validate_student(make(name="Abc")))
        self.assertNotIn("name", validate_student(make(name="Abcd")))

    def test_junk_names_rejected(self):
        for bad in ("s----", "----", "a - b", "Ab--cd", "Tom  Lee", "...."):
            self.assertIn("name", validate_student(make(name=bad)), bad)

    def test_real_names_accepted(self):
        for good in ("Mary-Jane Watson", "O'Brien", "J. Smith", "Tashi Dorji", "Li Ng"):
            self.assertNotIn("name", validate_student(make(name=good)), good)

    def test_junk_roll_rejected(self):
        for bad in ("---", "a--b", "-CS1", "CS1-", "CS 101"):
            self.assertIn("roll_no", validate_student(make(roll_no=bad)), bad)
        self.assertNotIn("roll_no", validate_student(make(roll_no="CS-101")))

    def test_junk_email_rejected(self):
        for bad in ("a@b", "@x.com", "a@x.c", "a b@x.com", ".a@x.com"):
            self.assertIn("email", validate_student(make(email=bad)), bad)

    def test_digits_in_name(self):
        self.assertIn("name", validate_student(make(name="R2D2")))

    def test_bad_email(self):
        self.assertIn("email", validate_student(make(email="not-an-email")))

    def test_unknown_course(self):
        errs = validate_student(make(course="Underwater Basket Weaving"))
        self.assertIn("course", errs)
        self.assertIn("not a valid course", errs["course"])

    def test_empty_course(self):
        self.assertIn("course", validate_student(make(course="")))

    def test_bad_roll(self):
        self.assertIn("roll_no", validate_student(make(roll_no="a b")))

    def test_marks_out_of_range(self):
        errs = validate_student(make(math=101, english=-1))
        self.assertIn("math", errs)
        self.assertIn("english", errs)

    def test_semester_out_of_range(self):
        self.assertIn("semester", validate_student(make(semester=9)))

    def test_grades(self):
        self.assertEqual([grade_for(p) for p in (85, 75, 65, 55, 10)], list("ABCDF"))

    def test_pass_rule(self):
        self.assertTrue(make(math=40, programming=40, english=40).passed)
        self.assertFalse(make(math=39).passed)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = StudentDB(":memory:")

    def tearDown(self):
        self.db.close()

    def test_add_and_get(self):
        sid = self.db.add(make())
        got = self.db.get(sid)
        self.assertEqual(got.name, "Test Student")
        self.assertEqual(got.total, 240)

    def test_duplicate_roll_rejected(self):
        self.db.add(make())
        with self.assertRaises(DuplicateRollError):
            self.db.add(make(name="Someone Else"))

    def test_update(self):
        sid = self.db.add(make())
        self.db.update(sid, make(name="Renamed Person", math=100))
        got = self.db.get(sid)
        self.assertEqual((got.name, got.math), ("Renamed Person", 100))

    def test_delete(self):
        sid = self.db.add(make())
        self.db.delete(sid)
        self.assertIsNone(self.db.get(sid))
        self.assertEqual(self.db.count(), 0)

    def test_search_text_course_and_percentage(self):
        self.db.add(make(roll_no="CS-1", name="Alpha One", math=90, programming=90, english=90))
        self.db.add(make(roll_no="EL-2", name="Beta Two", course="Electronics",
                         math=50, programming=50, english=50))
        self.assertEqual(len(self.db.search("alpha")), 1)
        self.assertEqual(len(self.db.search(course="Electronics")), 1)
        self.assertEqual([s.roll_no for s in self.db.search(min_pct=80)], ["CS-1"])
        self.assertEqual(len(self.db.search()), 2)

    def test_search_wildcards_are_literal(self):
        self.db.add(make())
        self.assertEqual(self.db.search("%"), [])

    def test_sql_injection_string_is_harmless(self):
        self.db.add(make())
        self.db.search("'; DROP TABLE students; --")
        self.assertEqual(self.db.count(), 1)

    def test_export_csv(self):
        self.db.add(make())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            self.assertEqual(self.db.export_csv(path), 1)
            with open(path, newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "CS-900")


class PersistenceTests(unittest.TestCase):
    def test_data_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "s.db")
            db = StudentDB(path)
            db.add(make())
            db.close()
            db2 = StudentDB(path)
            self.assertEqual(db2.count(), 1)
            db2.close()


if __name__ == "__main__":
    unittest.main()
