"""UI layer: the PyQt6 main window. All business rules live in logic.py / database.py."""

import sqlite3

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QAction, QKeySequence, QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QRadioButton, QSlider, QSpinBox, QSplitter,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from config import APP_TITLE, ROLL_NUMBER, STUDENT_NAME
from database import DuplicateRollError, StudentDB
from logic import COURSES, GENDERS, SUBJECTS, Student, grade_for, validate_student

TABLE_HEADERS = ["Roll No", "Name", "Email", "Course", "Sem", "Total", "%", "Grade"]


class MainWindow(QMainWindow):
    def __init__(self, db: StudentDB):
        super().__init__()
        self.db = db
        self.selected_id: int | None = None

        # ---- main window: title (with name/roll no), size, minimum size ----
        self.setWindowTitle(f"{APP_TITLE} - {STUDENT_NAME} ({ROLL_NUMBER})")
        self.resize(1120, 700)
        self.setMinimumSize(920, 580)

        self._build_menu()
        self._build_ui()
        self._connect_signals()
        self.refresh_table()
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------ menu
    def _build_menu(self):
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")
        self.export_action = QAction("&Export to CSV...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = bar.addMenu("&Edit")
        self.clear_action = QAction("&Clear form", self)
        self.clear_action.setShortcut(QKeySequence("Ctrl+L"))
        edit_menu.addAction(self.clear_action)

        help_menu = bar.addMenu("&Help")
        self.about_action = QAction("&About", self)
        help_menu.addAction(self.about_action)

    # -------------------------------------------------------------------- UI
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)                         # layout 1: QHBoxLayout
        outer.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_form_panel())
        splitter.addWidget(self._build_table_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 740])
        outer.addWidget(splitter)

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)                          # layout 2: QVBoxLayout
        layout.setContentsMargins(0, 0, 8, 0)

        box = QGroupBox("Student details")
        form = QFormLayout(box)                              # layout 3: QFormLayout
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # QLineEdit x3 (+ input mask via validator on roll number)
        self.roll_edit = QLineEdit()
        self.roll_edit.setPlaceholderText("e.g. CS-101")
        self.roll_edit.setMaxLength(20)
        self.roll_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"[A-Za-z0-9\-/]{0,20}")))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Full name")
        self.name_edit.setMaxLength(60)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("name@example.com")

        # QComboBox + QSpinBox
        self.course_combo = QComboBox()
        self.course_combo.addItems(COURSES)
        self.course_combo.setEditable(True)                  # user may type; validated live
        self.course_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.course_combo.setCurrentIndex(-1)
        self.course_combo.lineEdit().setPlaceholderText("Select or type a course...")
        self.sem_spin = QSpinBox()
        self.sem_spin.setRange(1, 8)

        # QRadioButton group
        gender_row = QHBoxLayout()
        self.gender_group = QButtonGroup(self)
        self.gender_buttons: dict[str, QRadioButton] = {}
        for g in GENDERS:
            rb = QRadioButton(g)
            self.gender_group.addButton(rb)
            self.gender_buttons[g] = rb
            gender_row.addWidget(rb)
        self.gender_buttons[GENDERS[0]].setChecked(True)

        # QCheckBox
        self.scholarship_check = QCheckBox("Receives scholarship")

        form.addRow("Roll No *", self.roll_edit)
        form.addRow("Name *", self.name_edit)
        form.addRow("Email *", self.email_edit)
        form.addRow("Course *", self.course_combo)
        form.addRow("Semester", self.sem_spin)
        form.addRow("Gender", gender_row)
        form.addRow("", self.scholarship_check)

        # Marks in a QGridLayout (layout 4)
        marks_box = QGroupBox("Marks (0-100)")
        grid = QGridLayout(marks_box)
        self.mark_spins: dict[str, QSpinBox] = {}
        for col, (key, label) in enumerate(zip(("math", "programming", "english"), SUBJECTS)):
            spin = QSpinBox()
            spin.setRange(0, 100)
            self.mark_spins[key] = spin
            grid.addWidget(QLabel(label), 0, col, Qt.AlignmentFlag.AlignHCenter)
            grid.addWidget(spin, 1, col)
        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.preview_label, 2, 0, 1, 3)

        # QTextEdit
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("Remarks (optional, max 300 chars)")
        self.remarks_edit.setFixedHeight(64)

        # Inline error feedback
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        # Buttons
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("deleteButton")
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearButton")
        for b in (self.add_btn, self.update_btn, self.delete_btn, self.clear_btn):
            btn_row.addWidget(b)

        layout.addWidget(box)
        layout.addWidget(marks_box)
        layout.addWidget(self.remarks_edit)
        layout.addWidget(self.error_label)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        # widget lookup used for highlighting invalid fields
        self.field_widgets: dict[str, QWidget] = {
            "roll_no": self.roll_edit, "name": self.name_edit, "email": self.email_edit,
            "course": self.course_combo, "semester": self.sem_spin,
            "math": self.mark_spins["math"], "programming": self.mark_spins["programming"],
            "english": self.mark_spins["english"], "remarks": self.remarks_edit,
        }
        self._update_preview()
        return panel

    def _build_table_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)

        # search / filter row
        filter_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search roll no, name or email...")
        self.search_edit.setClearButtonEnabled(True)
        self.course_filter = QComboBox()
        self.course_filter.addItem("All")
        self.course_filter.addItems(COURSES)
        self.pct_slider = QSlider(Qt.Orientation.Horizontal)
        self.pct_slider.setRange(0, 100)
        self.pct_slider.setSingleStep(5)
        self.pct_slider.setPageStep(10)
        self.pct_label = QLabel("Min %: 0")
        self.pct_label.setMinimumWidth(62)
        filter_row.addWidget(self.search_edit, 3)
        filter_row.addWidget(self.course_filter, 2)
        filter_row.addWidget(self.pct_slider, 2)
        filter_row.addWidget(self.pct_label)

        # table
        self.table = QTableWidget(0, len(TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(TABLE_HEADERS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # summary row: label + progress bar
        summary_row = QHBoxLayout()
        self.summary_label = QLabel()
        self.summary_label.setObjectName("summaryLabel")
        self.avg_bar = QProgressBar()
        self.avg_bar.setRange(0, 100)
        self.avg_bar.setFormat("Average %p%")
        self.avg_bar.setFixedWidth(220)
        summary_row.addWidget(self.summary_label, 1)
        summary_row.addWidget(self.avg_bar)

        layout.addLayout(filter_row)
        layout.addWidget(self.table, 1)
        layout.addLayout(summary_row)
        return panel

    # --------------------------------------------------------------- signals
    def _connect_signals(self):
        # Signal -> slot wiring (>= 5 handled events)
        self.add_btn.clicked.connect(self.on_add)
        self.update_btn.clicked.connect(self.on_update)
        self.delete_btn.clicked.connect(self.on_delete)
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_action.triggered.connect(self.clear_form)
        self.export_action.triggered.connect(self.on_export)
        self.about_action.triggered.connect(self.show_about)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.search_edit.textChanged.connect(self.refresh_table)
        self.course_filter.currentIndexChanged.connect(self.refresh_table)
        self.pct_slider.valueChanged.connect(self.on_slider_changed)
        for spin in self.mark_spins.values():
            spin.valueChanged.connect(self._update_preview)
        # live validation: red outline appears while typing
        for edit in (self.roll_edit, self.name_edit, self.email_edit):
            edit.textChanged.connect(self._live_validate)
        self.course_combo.currentTextChanged.connect(self._live_validate)

    # ------------------------------------------------------------ form <-> model
    def read_form(self) -> Student:
        gender = next((g for g, rb in self.gender_buttons.items() if rb.isChecked()), "")
        typed = " ".join(self.course_combo.currentText().split())
        # accept any capitalisation of a real course; keep unknown text so validation rejects it
        course = next((c for c in COURSES if c.lower() == typed.lower()), typed)
        return Student(
            id=self.selected_id,
            roll_no=self.roll_edit.text().strip(),
            name=" ".join(self.name_edit.text().split()),
            email=self.email_edit.text().strip(),
            course=course,
            semester=self.sem_spin.value(),
            gender=gender,
            scholarship=self.scholarship_check.isChecked(),
            math=self.mark_spins["math"].value(),
            programming=self.mark_spins["programming"].value(),
            english=self.mark_spins["english"].value(),
            remarks=self.remarks_edit.toPlainText().strip(),
        )

    def fill_form(self, s: Student):
        self.roll_edit.setText(s.roll_no)
        self.name_edit.setText(s.name)
        self.email_edit.setText(s.email)
        self.course_combo.setCurrentText(s.course)
        self.sem_spin.setValue(s.semester)
        self.gender_buttons.get(s.gender, self.gender_buttons[GENDERS[0]]).setChecked(True)
        self.scholarship_check.setChecked(s.scholarship)
        self.mark_spins["math"].setValue(s.math)
        self.mark_spins["programming"].setValue(s.programming)
        self.mark_spins["english"].setValue(s.english)
        self.remarks_edit.setPlainText(s.remarks)
        self._show_errors({})

    def clear_form(self):
        self.selected_id = None
        self.table.clearSelection()
        self.roll_edit.clear()
        self.name_edit.clear()
        self.email_edit.clear()
        self.course_combo.setCurrentIndex(-1)
        self.course_combo.lineEdit().clear()
        self.sem_spin.setValue(1)
        self.gender_buttons[GENDERS[0]].setChecked(True)
        self.scholarship_check.setChecked(False)
        for spin in self.mark_spins.values():
            spin.setValue(0)
        self.remarks_edit.clear()
        self._show_errors({})
        self._update_buttons()
        self.roll_edit.setFocus()

    # ----------------------------------------------------------------- slots
    def on_add(self):
        student = self.read_form()
        student.id = None
        if not self._validate(student):
            return
        try:
            self.db.add(student)
        except DuplicateRollError:
            self._show_errors({"roll_no": f"Roll number '{student.roll_no}' already exists."})
            QMessageBox.warning(self, "Duplicate roll number",
                                f"A student with roll number '{student.roll_no}' already exists.")
            return
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Database error", f"Could not save the student:\n{exc}")
            return
        self.clear_form()
        self.refresh_table()
        self.statusBar().showMessage(f"Added {student.name}", 4000)

    def on_update(self):
        if self.selected_id is None:
            QMessageBox.information(self, "No selection", "Select a student in the table first.")
            return
        student = self.read_form()
        if not self._validate(student):
            return
        try:
            self.db.update(self.selected_id, student)
        except DuplicateRollError:
            self._show_errors({"roll_no": f"Roll number '{student.roll_no}' belongs to another student."})
            return
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Database error", f"Could not update the student:\n{exc}")
            return
        self.clear_form()
        self.refresh_table()
        self.statusBar().showMessage(f"Updated {student.name}", 4000)

    def on_delete(self):
        if self.selected_id is None:
            return
        student = self.db.get(self.selected_id)
        if student is None:
            return
        answer = QMessageBox.question(
            self, "Confirm delete",
            f"Delete {student.name} ({student.roll_no})?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.db.delete(self.selected_id)
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Database error", f"Could not delete the student:\n{exc}")
            return
        self.clear_form()
        self.refresh_table()
        self.statusBar().showMessage(f"Deleted {student.name}", 4000)

    def on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.selected_id = None
        else:
            item = self.table.item(rows[0].row(), 0)
            self.selected_id = item.data(Qt.ItemDataRole.UserRole)
            student = self.db.get(self.selected_id)
            if student:
                self.fill_form(student)
        self._update_buttons()

    def on_slider_changed(self, value: int):
        self.pct_label.setText(f"Min %: {value}")
        self.refresh_table()

    def on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export students", "students.csv",
                                              "CSV files (*.csv)")
        if not path:
            return
        try:
            n = self.db.export_csv(path, self._current_filter_results())
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", f"Could not write the file:\n{exc}")
            return
        self.statusBar().showMessage(f"Exported {n} students", 5000)

    def show_about(self):
        QMessageBox.about(
            self, f"About {APP_TITLE}",
            f"<b>{APP_TITLE}</b><br>Unit V assignment - PyQt6 + SQLite<br><br>"
            f"Student: {STUDENT_NAME}<br>Roll No: {ROLL_NUMBER}",
        )

    # --------------------------------------------------------------- helpers
    def _validate(self, student: Student) -> bool:
        errors = validate_student(student)
        self._show_errors(errors)
        return not errors

    def _show_errors(self, errors: dict[str, str], focus: bool = True):
        """Show messages and outline invalid widgets in red (via the 'invalid' QSS property)."""
        for key, widget in self.field_widgets.items():
            widget.setProperty("invalid", key in errors)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.error_label.setText("\n".join(errors.values()))
        if focus:
            for key, widget in self.field_widgets.items():
                if key in errors:
                    widget.setFocus()
                    break

    def _live_validate(self):
        """Validate roll no / name / email while typing. Empty fields are left alone
        (the Add button reports 'required'), so the user is not nagged before typing."""
        texts = {
            "roll_no": self.roll_edit.text(), "name": self.name_edit.text(),
            "email": self.email_edit.text(), "course": self.course_combo.currentText(),
        }
        errors = validate_student(self.read_form())
        shown = {k: msg for k, msg in errors.items() if k in texts and texts[k].strip()}
        self._show_errors(shown, focus=False)

    def _update_preview(self):
        total = sum(spin.value() for spin in self.mark_spins.values())
        pct = total / len(SUBJECTS)
        self.preview_label.setText(f"Total {total}/300  |  {pct:.1f}%  |  Grade {grade_for(pct)}")

    def _update_buttons(self):
        has_selection = self.selected_id is not None
        self.update_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _current_filter_results(self) -> list[Student]:
        return self.db.search(self.search_edit.text(), self.course_filter.currentText(),
                              self.pct_slider.value())

    def refresh_table(self):
        students = self._current_filter_results()
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(students))
        for row, s in enumerate(students):
            cells = [s.roll_no, s.name, s.email, s.course, s.semester, s.total,
                     round(s.percentage, 1), s.grade]
            for col, value in enumerate(cells):
                item = QTableWidgetItem()
                item.setData(Qt.ItemDataRole.DisplayRole, value)   # ints/floats sort numerically
                if col in (4, 5, 6, 7):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, s.id)
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)

        # rebuilding the rows drops the selection, so Update/Delete are disabled again
        self.selected_id = None
        self._update_buttons()

        average = sum(s.percentage for s in students) / len(students) if students else 0
        self.avg_bar.setValue(round(average))
        self.summary_label.setText(f"Showing {len(students)} of {self.db.count()} students")

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
