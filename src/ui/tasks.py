import logging
import random
import sys
import re
from typing import Dict, Any, Optional
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from PyQt5.QtWidgets import (QFrame, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QStackedWidget, QRadioButton, QCheckBox, QLineEdit, QTextEdit,
    QListWidget, QPlainTextEdit, QMessageBox, QScrollArea, QListWidgetItem, QSizePolicy, QTextBrowser)
from PyQt5.QtCore import Qt, QMimeData, QSize, QTimer, QRegularExpression, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap, QIcon, QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .lesson_win import *
from .fortune_wheel import FortuneWheel
from src.services.lesson_service import LessonService
from src.services.user_service import UserService
from src.services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self._rules = []

        kw = QTextCharFormat()
        kw.setForeground(QColor("#569CD6"))
        kw.setFontWeight(QFont.Bold)
        

        builtins = QTextCharFormat()
        builtins.setForeground(QColor("#C586C0"))

        string = QTextCharFormat()
        string.setForeground(QColor("#6A9955"))

        comment = QTextCharFormat()
        comment.setForeground(QColor("#6B7280"))
        comment.setFontItalic(True)

        number = QTextCharFormat()
        number.setForeground(QColor("#B5CEA8"))

        decorator = QTextCharFormat()
        decorator.setForeground(QColor("#DCDCAA"))

        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
            "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield",
        ]
        for k in keywords:
            self._rules.append((QRegularExpression(rf"\\b{k}\\b"), kw))

        builtin_names = [
            "print", "len", "range", "input", "int", "float", "str", "bool", "list", "dict", "set", "tuple",
            "sum", "min", "max", "abs", "round", "enumerate", "zip", "map", "filter",
        ]
        for b in builtin_names:
            self._rules.append((QRegularExpression(rf"\\b{b}\\b"), builtins))

        self._rules.append((QRegularExpression(r"@[A-Za-z_][A-Za-z0-9_]*"), decorator))
        self._rules.append((QRegularExpression(r"\\b[0-9]+(\\.[0-9]+)?\\b"), number))
        self._rules.append((QRegularExpression(r"#.*"), comment))
        self._rules.append((QRegularExpression(r'"[^"\\n]*"'), string))
        self._rules.append((QRegularExpression(r"'[^'\\n]*'"), string))

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

class DraggableLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setProperty("type", "lb_name_course")
        self.setMinimumWidth(100)
        self.setFixedSize(200, 75)

    def mousePressEvent(self, event):
        mime_data = QMimeData()
        mime_data.setText(self.text())

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)


class DropLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setProperty("type", "lb_name_course")
        self.setMinimumWidth(150)
        self.setFixedSize(200, 75)
        self.setAlignment(Qt.AlignCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.setText(event.mimeData().text())
        event.acceptProposedAction()


class TaskWindow(QWidget):
    points_updated = pyqtSignal(int)
    lesson_completed = pyqtSignal(int, int, int)  # correct, total, percentage

    def __init__(self):
        super().__init__()
        self.lesson_content = {}
        self.user_id = None
        self.course_id = None
        self.lesson_id = None
        self._lesson_service = LessonService()
        self._user_service = UserService()
        from src.services.progress_service import ProgressService
        self._progress_service = ProgressService()
        self.test_buttons = []
        self.content_progress = {}
        self.progress_callback = None
        self.question_states = {}  # {question_id: {"answered": bool, "correct": bool, "score": float}}
        self.user_answers = {}
        self._highlighters = []
        self._awarded_questions = set()
        self._is_retake = False
        self._start_time = None

    def set_context(self, user_id: str = None, course_id: str = None, lesson_id: str = None):
        """Set identifiers needed for saving lesson/content progress."""
        self.user_id = user_id
        self.course_id = course_id
        self.lesson_id = lesson_id
        self._check_if_retake()

    def _check_if_retake(self):
        """Check if this lesson has already been completed (retake)."""
        if not self.user_id or not self.lesson_id:
            return
        try:
            import uuid
            user_uuid = uuid.UUID(self.user_id)
            lesson_uuid = uuid.UUID(self.lesson_id)
            from src.db import get_db
            db = next(get_db())
            from src.db.repositories.completed_lesson_repo import CompletedLessonRepository
            repo = CompletedLessonRepository()
            self._is_retake = repo.is_lesson_completed(db, user_uuid, lesson_uuid)
            if self._is_retake:
                logger.info(f"Lesson {self.lesson_id} is a retake - no points will be awarded")
        except Exception as e:
            logger.exception("Error checking if lesson is retake")

    def set_progress_callback(self, callback):
        """Set callback function to notify progress updates to parent (lesson_win)."""
        self.progress_callback = callback

    def update_content(self, lesson_content):
        self.lesson_content = lesson_content
        self._initialize_progress_tracking()
        self._update_overall_progress()
        import time
        self._start_time = time.time()
        logger.debug(
            "Initialized progress tracking with %s questions: %s",
            len(self.question_states),
            list(self.question_states.keys()),
        )
    
    def _initialize_progress_tracking(self):
        """Initialize progress tracking data structures for all content items."""
        self.content_progress = {}
        self.question_states = {}
        
        test_questions = self.lesson_content.get("test_questions", [])
        for i, q in enumerate(test_questions):
            q_id = q.get("id", f"test_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}
        
        for i, q in enumerate(self.lesson_content.get("true_false_questions", [])):
            q_id = q.get("id", f"tf_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}
        
        for i, q in enumerate(self.lesson_content.get("input_questions", [])):
            q_id = q.get("id", f"input_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}
        
        for i, q in enumerate(self.lesson_content.get("blank_questions", [])):
            q_id = q.get("id", f"blank_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}
        
        for i, q in enumerate(self.lesson_content.get("code_questions", [])):
            q_id = q.get("id", f"code_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}
        
        for i, q in enumerate(self.lesson_content.get("drag_and_drop_questions", [])):
            q_id = q.get("id", f"dd_q_{i}")
            self.question_states[q_id] = {"answered": False, "correct": False, "score": 0.0}

        for i, task in enumerate(self.lesson_content.get("interactive_tasks", [])):
            if task.get("type") == "tool":
                continue
            task_id = task.get("id") or task.get("task_id") or f"interactive_{i}"
            self.question_states[task_id] = {"answered": False, "correct": False, "score": 0.0}
    
    def _record_question_answer(self, question_id: str, is_correct: bool, score: float = 1.0):
        """Record an answer submission for a question and update progress."""
        
        if question_id in self.question_states:
            self.question_states[question_id]["answered"] = True
            self.question_states[question_id]["correct"] = is_correct
            self.question_states[question_id]["score"] = score if is_correct else 0.0
        else:
            self.question_states[question_id] = {
                "answered": True,
                "correct": is_correct,
                "score": score if is_correct else 0.0
            }
        
        if is_correct and question_id not in self._awarded_questions:
            self._award_points_for_correct_answer(question_id)
        
        self._update_overall_progress()

    def _award_points_for_correct_answer(self, question_id: str, points: int = 10):
        """Award points to the user for a correct answer."""
        if self._is_retake:
            logger.debug(f"Skipping points for {question_id} - lesson is a retake")
            return

        current_user = SessionManager.get_current_user()
        if not current_user:
            return
        
        user_id = current_user.get("id")
        if not user_id:
            return
        
        self._awarded_questions.add(question_id)
        new_total = self._user_service.add_points(user_id, points)
        
        current_user["points"] = new_total
        SessionManager.set_current_user(current_user)
        
        self.points_updated.emit(new_total)
        logger.info(f"Awarded {points} points for question {question_id}. New total: {new_total}")

    def _update_overall_progress(self):
        """Calculate and update overall lesson progress."""
        total_questions = len(self.question_states)
        if total_questions == 0:
            return
        
        answered = sum(1 for q in self.question_states.values() if q["answered"])
        correct = sum(1 for q in self.question_states.values() if q["correct"])
        total_score = sum(q["score"] for q in self.question_states.values())

        answered_percentage = int((answered / total_questions) * 100) if total_questions > 0 else 0
        correct_percentage = int((total_score / total_questions) * 100) if total_questions > 0 else 0

        if self.progress_callback:
            try:
                self.progress_callback(
                    answered=answered,
                    total=total_questions,
                    percentage=answered_percentage,
                    correct=correct,
                    correct_percentage=correct_percentage,
                )
            except Exception as e:
                logger.exception("Error calling progress callback")
    
    def get_current_progress(self) -> Dict[str, Any]:
        """Get current progress state."""
        total_questions = len(self.question_states)
        if total_questions == 0:
            return {"percentage": 0, "answered": 0, "correct": 0, "total": 0}
        
        answered = sum(1 for q in self.question_states.values() if q["answered"])
        correct = sum(1 for q in self.question_states.values() if q["correct"])
        total_score = sum(q["score"] for q in self.question_states.values())
        percentage = int((total_score / total_questions) * 100) if total_questions > 0 else 0
        
        return {
            "percentage": percentage,
            "answered": answered,
            "correct": correct,
            "total": total_questions
        }

    def _on_choice_toggled(self, qid: str, opt_text: str, corr, checked: bool):
        """Handler for option radio buttons (multiple choice / true-false).
        Only react when a button becomes checked.
        """
        if not checked:
            return
        try:
            norm_corr = corr
            if isinstance(corr, str):
                low = corr.strip().lower()
                if low in ("true", "правда", "так", "true", "yes"):
                    norm_corr = True
                elif low in ("false", "хибно", "неправда", "ні", "no"):
                    norm_corr = False
                else:
                    norm_corr = corr.strip()

            if isinstance(norm_corr, bool):
                opt_low = str(opt_text).strip().lower()
                opt_bool = opt_low in ("true", "правда", "так")
                if opt_low in ("false", "хибно", "неправда", "ні", "no"):
                    opt_bool = False
                is_correct = (opt_bool == norm_corr)
            else:
                is_correct = str(opt_text).strip() == str(norm_corr).strip()
        except Exception:
            is_correct = False

        self._record_question_answer(qid, is_correct, score=1.0 if is_correct else 0.0)

    def _on_input_finished(self, qid: str, line_edit: QLineEdit, corr):
        """Handler for input/blank fields when editing is finished."""
        user_text = line_edit.text().strip()
        self.user_answers[qid] = user_text
        if not user_text:
            if qid in self.question_states:
                self.question_states[qid]["answered"] = False
                self.question_states[qid]["correct"] = False
                self.question_states[qid]["score"] = 0.0
                self._update_overall_progress()
            return

        self._record_question_answer(qid, True, score=0.0)
    
    def _process_code_blocks(self, text):
        """Process markdown text and add syntax highlighting to code blocks"""
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        
        def highlight_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            
            try:
                if language:
                    lexer = get_lexer_by_name(language)
                else:
                    lexer = guess_lexer(code)
                
                formatter = HtmlFormatter(
                    style='default',
                    noclasses=True,
                    cssstyles=''
                )
                
                highlighted_code = highlight(code, lexer, formatter)
                
                return f'<div style="border: 1px solid #e9ecef; border-radius: 4px; padding: 10px; margin: 10px 0; overflow-x: auto;color:#414c50;"><pre>{highlighted_code}</pre></div>'
                
            except Exception as e:
                logger.warning("Could not highlight %s code: %s", language, e)
                return f'<div style="border: 1px solid #e9ecef; border-radius: 4px; padding: 10px; margin: 10px 0; color:#414c50;"><pre><code>{code}</code></pre></div>'
        
        processed_text = re.sub(code_block_pattern, highlight_code_block, text, flags=re.DOTALL)
        
        processed_text = self._basic_markdown_to_html(processed_text)
        
        return processed_text

    def _basic_markdown_to_html(self, text):
        """Convert basic markdown to HTML for non-code elements"""
        text = re.sub(r'^### (.*)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        text = re.sub(r'`(.*?)`', r'<code style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 3px; padding: 2px 4px; font-family: monospace; color: #e74c3c;">\1</code>', text)
        
        text = re.sub(r'^- (.*)$', r'<li>\1</li>', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)\. (.*)$', r'<li>\1. \2</li>', text, flags=re.MULTILINE)
        
        text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
        text = re.sub(r'(<ul>.*?</ul>)\s*<ul>', r'\1', text, flags=re.DOTALL)  # Merge consecutive ul tags
        
        text = re.sub(r'\n\n', '</p><p>', text)
        text = f'<p>{text}</p>'
        
        text = text.replace('<p></p>', '')
        text = text.replace('<p><h', '<h')
        text = text.replace('</h1></p>', '</h1>')
        text = text.replace('</h2></p>', '</h2>')
        text = text.replace('</h3></p>', '</h3>')
        text = text.replace('<p><ul>', '<ul>')
        text = text.replace('</ul></p>', '</ul>')
        text = text.replace('<p><div>', '<div>')
        text = text.replace('</div></p>', '</div>')
        
        return text

    
    def create_theory(self):
        widget = QWidget()
        layout = QVBoxLayout()

        theory_text = QTextBrowser()
        theory_text.setReadOnly(True)
        theory_text.setMinimumHeight(300)
        theory_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        theory = self.lesson_content.get("theory", "Теорія не знайдена")
        logger.debug("[create_theory] Processing theory with syntax highlighting")
        
        processed_theory = self._process_code_blocks(theory)
        
        theory_text.setHtml(processed_theory)
        
        layout.addWidget(theory_text)

        widget.setLayout(layout)
        return widget

    def create_tasks_tab(self):
        widget = QWidget()
        widget.setProperty("type", "w_pg")
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self.total_time = 120  
        self.time_left = self.total_time
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label = QLabel(f"{minutes:02d}:{seconds:02d}")
        self.timer_label.setProperty("task_role", "timer")
        layout.addWidget(self.timer_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000) 
        self.time_up_shown = False

        for i, q in enumerate(self.lesson_content.get("test_questions", [])):
            test_container = QFrame()
            test_container.setFrameShape(QFrame.StyledPanel)
            test_container.setProperty("task_role", "card")
            test_layout = QVBoxLayout(test_container)
            test_layout.setSpacing(8)
            
            test_q = QLabel(f"Питання {i+1}: {q.get('question', '')}")
            test_q.setProperty("type", "lb_description")
            test_q.setWordWrap(True)
            test_layout.addWidget(test_q)
            
            options = q.get("options", [])[:]
            random.shuffle(options)
            buttons = []
            correct_answer = q.get('answer')
            qid = q.get('id', f"test_q_{i}")
            for opt in options:
                btn = QRadioButton(opt)
                btn.toggled.connect(lambda checked, qid=qid, opt_text=opt, corr=correct_answer: self._on_choice_toggled(qid, opt_text, corr, checked))
                buttons.append(btn)
                test_layout.addWidget(btn)
            self.test_buttons.append(buttons)
            layout.addWidget(test_container)

        for i, q in enumerate(self.lesson_content.get("true_false_questions", [])):
            tf_container = QFrame()
            tf_container.setFrameShape(QFrame.StyledPanel)
            tf_container.setProperty("task_role", "card")
            tf_layout = QVBoxLayout(tf_container)
            tf_layout.setSpacing(8)
            
            tf_q = QLabel(f"{q.get('question', '')}")
            tf_q.setProperty("type", "lb_description")
            tf_q.setWordWrap(True)
            tf_layout.addWidget(tf_q)
            
            cb_true = QRadioButton("Правда")
            cb_false = QRadioButton("Неправда")
            tf_id = q.get('id', f"tf_q_{i}")
            corr = q.get('answer', True)
            cb_true.toggled.connect(lambda checked, qid=tf_id, corr=corr: self._on_choice_toggled(qid, 'Правда', corr, checked))
            cb_false.toggled.connect(lambda checked, qid=tf_id, corr=corr: self._on_choice_toggled(qid, 'Неправда', corr, checked))
            tf_layout.addWidget(cb_true)
            tf_layout.addWidget(cb_false)
            layout.addWidget(tf_container)

        for i, q in enumerate(self.lesson_content.get("input_questions", [])):
            input_container = QFrame()
            input_container.setFrameShape(QFrame.StyledPanel)
            input_container.setProperty("task_role", "card-info")
            input_layout = QVBoxLayout(input_container)
            input_layout.setSpacing(10)
            
            input_q = QLabel(f"Завдання {i+1}: {q.get('question', '')}")
            input_q.setProperty("type", "lb_description")
            input_q.setWordWrap(True)
            input_layout.addWidget(input_q)
            
            input_answer = QLineEdit()
            input_answer.setProperty("type", "tasks")
            input_answer.setFixedHeight(40)
            input_answer.setPlaceholderText("Введіть відповідь...")
            input_layout.addWidget(input_answer)
            
            input_id = q.get('id', f"input_q_{i}")
            correct_answer = q.get('answer', '')
            input_answer.editingFinished.connect(lambda qid=input_id, le=input_answer, corr=correct_answer: self._on_input_finished(qid, le, corr))
            input_answer.returnPressed.connect(lambda qid=input_id, le=input_answer, corr=correct_answer: self._on_input_finished(qid, le, corr))

            if q.get('hints'):
                self._add_hidden_hints(input_layout, q.get('hints', []))

            layout.addWidget(input_container)

        for i, q in enumerate(self.lesson_content.get("blank_questions", [])):
            blank_container = QFrame()
            blank_container.setFrameShape(QFrame.StyledPanel)
            blank_container.setProperty("task_role", "card-warning")
            blank_layout = QVBoxLayout(blank_container)
            blank_layout.setSpacing(10)
            
            blank_q = QLabel(f"Заповніть пропуск: {q.get('question', '')} {q.get('question_part2', '')}")
            blank_q.setProperty("type", "lb_description")
            blank_q.setWordWrap(True)
            blank_layout.addWidget(blank_q)
            
            input_blank = QLineEdit()
            input_blank.setProperty("type", "tasks")
            input_blank.setFixedHeight(40)
            input_blank.setPlaceholderText("Заповніть пропуск...")
            blank_layout.addWidget(input_blank)
            
            blank_id = q.get('id', f"blank_q_{i}")
            blank_corr = q.get('answer', '')
            input_blank.editingFinished.connect(lambda qid=blank_id, le=input_blank, corr=blank_corr: self._on_input_finished(qid, le, corr))
            input_blank.returnPressed.connect(lambda qid=blank_id, le=input_blank, corr=blank_corr: self._on_input_finished(qid, le, corr))

            if q.get('hints'):
                self._add_hidden_hints(blank_layout, q.get('hints', []))

            layout.addWidget(blank_container)

        for i, q in enumerate(self.lesson_content.get("code_questions", [])):
            code_container = QFrame()
            code_container.setFrameShape(QFrame.StyledPanel)
            code_container.setProperty("task_role", "card")
            code_layout = QVBoxLayout(code_container)
            code_layout.setSpacing(10)
            
            code_q = QLabel(f"Завдання {i+1}: {q.get('question', '')}")
            code_q.setProperty("type", "lb_description")
            code_q.setWordWrap(True)
            code_layout.addWidget(code_q)
            
            code_box = QTextEdit(q.get("code", ""))
            code_box.setMinimumHeight(120)
            code_box.setPlaceholderText("Напишіть ваш код тут...")
            code_box.setProperty("task_role", "code_editor")
            code_layout.addWidget(code_box)

            self._highlighters.append(PythonHighlighter(code_box.document()))

            code_id = q.get('id', f"code_q_{i}")
            expected_answer = q.get('answer', '')

            def _on_code_change():
                user_raw = code_box.toPlainText() or ""
                self.user_answers[code_id] = user_raw
                if user_raw.strip():
                    self._record_question_answer(code_id, True, 0.0)
                else:
                    if code_id in self.question_states:
                        self.question_states[code_id]["answered"] = False
                        self.question_states[code_id]["correct"] = False
                        self.question_states[code_id]["score"] = 0.0
                        self._update_overall_progress()

            code_box.textChanged.connect(_on_code_change)
            
            if q.get('hints'):
                hints_container = QWidget()
                hints_layout = QVBoxLayout(hints_container)
                hints_layout.setContentsMargins(0, 0, 0, 0)
                hints_layout.setSpacing(5)
                
                hints_text = QLabel("••••••••••••••••••••••••••••••")
                hints_text.setProperty("task_role", "hint_label")
                hints_text.setProperty("hint_state", "hidden")
                hints_text.setWordWrap(True)
                hints_text.setProperty("hidden_text", ", ".join(q.get('hints', [])))
                
                show_hints_btn = QPushButton("👁 Показати підказки")
                show_hints_btn.setFixedWidth(160)
                show_hints_btn.setProperty("task_role", "hint_button")
                show_hints_btn.setCheckable(True)
                show_hints_btn.clicked.connect(lambda checked, lbl=hints_text, btn=show_hints_btn: self._toggle_hints(checked, lbl, btn))
                
                hints_header = QHBoxLayout()
                hint_title = QLabel("Підказки:")
                hint_title.setProperty("task_role", "hint_title")
                hints_header.addWidget(hint_title)
                hints_header.addWidget(show_hints_btn)
                hints_header.addStretch()
                
                hints_layout.addLayout(hints_header)
                hints_layout.addWidget(hints_text)
                code_layout.addWidget(hints_container)
            
            layout.addWidget(code_container)

        for i, q in enumerate(self.lesson_content.get("fix_error_questions", [])):
            fix_container = QFrame()
            fix_container.setFrameShape(QFrame.StyledPanel)
            fix_container.setProperty("task_role", "card")
            fix_layout = QVBoxLayout(fix_container)
            fix_layout.setSpacing(10)
            
            fix_q = QLabel(f"Виправте помилку {i+1}: {q.get('question', '')}")
            fix_q.setProperty("type", "lb_description")
            fix_q.setWordWrap(True)
            fix_layout.addWidget(fix_q)
            
            code_box = QTextEdit(q.get("code", ""))
            code_box.setMinimumHeight(120)
            code_box.setProperty("task_role", "code_editor")
            fix_layout.addWidget(code_box)

            self._highlighters.append(PythonHighlighter(code_box.document()))

            fix_id = q.get('id', f"fix_q_{i}")

            def _on_fix_change():
                user_raw = code_box.toPlainText() or ""
                self.user_answers[fix_id] = user_raw
                if user_raw.strip():
                    self._record_question_answer(fix_id, True, 0.0)
                else:
                    if fix_id in self.question_states:
                        self.question_states[fix_id]["answered"] = False
                        self.question_states[fix_id]["correct"] = False
                        self.question_states[fix_id]["score"] = 0.0
                        self._update_overall_progress()

            code_box.textChanged.connect(_on_fix_change)
            
            if q.get('hints'):
                hints_container = QWidget()
                hints_layout = QVBoxLayout(hints_container)
                hints_layout.setContentsMargins(0, 0, 0, 0)
                hints_layout.setSpacing(5)
                
                hints_text = QLabel("••••••••••••••••••••••••••••••")
                hints_text.setProperty("task_role", "hint_label")
                hints_text.setProperty("hint_state", "hidden")
                hints_text.setWordWrap(True)
                hints_text.setProperty("hidden_text", ", ".join(q.get('hints', [])))
                
                show_hints_btn = QPushButton("👁 Показати підказки")
                show_hints_btn.setFixedWidth(160)
                show_hints_btn.setProperty("task_role", "hint_button")
                show_hints_btn.setCheckable(True)
                show_hints_btn.clicked.connect(lambda checked, lbl=hints_text, btn=show_hints_btn: self._toggle_hints(checked, lbl, btn))
                
                hints_header = QHBoxLayout()
                hint_title = QLabel("Підказки:")
                hint_title.setProperty("task_role", "hint_title")
                hints_header.addWidget(hint_title)
                hints_header.addWidget(show_hints_btn)
                hints_header.addStretch()
                
                hints_layout.addLayout(hints_header)
                hints_layout.addWidget(hints_text)
                fix_layout.addWidget(hints_container)
            
            layout.addWidget(fix_container)

        for i, q in enumerate(self.lesson_content.get("drag_and_drop_questions", [])):
            if not q.get("words"):
                continue
            dd_container = QFrame()
            dd_container.setFrameShape(QFrame.StyledPanel)
            dd_container.setProperty("task_role", "card")
            dd_main_layout = QVBoxLayout(dd_container)
            dd_main_layout.setSpacing(16)
            
            dd_q = QLabel(f"{q.get('question', '')}")
            dd_q.setProperty("type", "lb_description")
            dd_q.setWordWrap(True)
            dd_main_layout.addWidget(dd_q)
            
            descriptions = q.get("descriptions", [])
            words = q.get("words", [])
            self.drop_labels = []

            drop_layout = QHBoxLayout()
            drop_layout.setSpacing(12)
            for desc in descriptions:
                drop_item_container = QVBoxLayout()
                drop_item_container.setSpacing(8)
                label_desc = QLabel(desc)
                label_desc.setWordWrap(True)
                label_desc.setAlignment(Qt.AlignCenter)
                label_desc.setProperty("type", "lb_small")
                drop_label = DropLabel()
                drop_item_container.addWidget(label_desc)
                drop_item_container.addWidget(drop_label)
                self.drop_labels.append(drop_label)
                drop_layout.addLayout(drop_item_container)

            drag_layout = QHBoxLayout()
            drag_layout.setSpacing(12)
            for word in words:
                drag_layout.addWidget(DraggableLabel(word))

            dd_main_layout.addLayout(drop_layout)
            dd_main_layout.addLayout(drag_layout)
            layout.addWidget(dd_container)

        for task in self.lesson_content.get("interactive_tasks", []):
            task_type = task.get("type", "")
            task_id = task.get("id") or task.get("task_id") or str(id(task))
            title = task.get("title", "Інтерактивне завдання")
            instructions = task.get("instructions", "")
            config = task.get("configuration", {})
            
            interactive_container = QFrame()
            interactive_container.setFrameShape(QFrame.StyledPanel)
            interactive_container.setProperty("task_role", "card-interactive")
            interactive_layout = QVBoxLayout(interactive_container)
            interactive_layout.setSpacing(12)
            
            title_label = QLabel(title)
            title_label.setProperty("task_role", "section_title")
            interactive_layout.addWidget(title_label)
            
            if instructions:
                instr_label = QLabel(instructions)
                instr_label.setWordWrap(True)
                instr_label.setProperty("task_role", "placeholder_label")
                interactive_layout.addWidget(instr_label)
            
            if task_type == "simulation" and config.get("simulation_type") == "graph_plot":
                self._create_graph_widget(interactive_layout, config)
            elif task_type == "visualization" and config.get("visualization_type") == "geometry":
                self._create_geometry_widget(interactive_layout, config)
            else:
                placeholder = QLabel(f"Інтерактивний елемент: {task_type}")
                placeholder.setStyleSheet("color: #888; padding: 20px;")
                interactive_layout.addWidget(placeholder)
            
            layout.addWidget(interactive_container)

        finish_btn = QPushButton("✓ Завершити та перевірити")
        finish_btn.setMinimumHeight(50)
        finish_btn.setProperty("type", "start_continue")
        finish_btn.clicked.connect(self._finish_exercises)
        layout.addWidget(finish_btn)

        layout.addStretch()
        return widget
    def _create_graph_widget(self, parent_layout, config):
        """Create graph plotting widget with matplotlib"""
        import numpy as np
        
        graph_frame = QFrame()
        graph_frame.setProperty("task_role", "card")
        graph_layout = QVBoxLayout(graph_frame)
        
        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#f8f9fa')
        ax = fig.add_subplot(111)
        
        initial_state = config.get("initial_state", {})
        domain = initial_state.get("domain", [-10, 10])
        y_range = initial_state.get("range", [-10, 10])
        equations = initial_state.get("equations", [])
        
        x = np.linspace(domain[0], domain[1], 400)
        
        for eq_data in equations:
            eq_str = eq_data.get("equation", "")
            color = eq_data.get("color", "#3498db")
            
            try:
                if "y = " in eq_str or "y=" in eq_str:
                    expr = eq_str.replace("y = ", "").replace("y=", "").strip()
                    expr = expr.replace("^", "**")
                    import re
                    expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
                    expr = re.sub(r'([a-zA-Z])(\d)', r'\1*\2', expr)
                    y = eval(expr, {"x": x, "np": np, "__builtins__": {}})
                    ax.plot(x, y, color=color, linewidth=2, label=eq_str)
            except Exception as e:
                logger.warning("Error plotting %s: %s", eq_str, e)
        
        ax.set_xlim(domain)
        ax.set_ylim(y_range)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.legend(loc='upper right', fontsize=9)
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(500, 350)
        graph_layout.addWidget(canvas)
        
        parent_layout.addWidget(graph_frame)
        
        tasks = config.get("tasks", [])
        if tasks:
            tasks_label = QLabel("Завдання:")
            tasks_label.setProperty("task_role", "section_header")
            parent_layout.addWidget(tasks_label)
            
            for i, t in enumerate(tasks):
                t_frame = QFrame()
                t_frame.setProperty("task_role", "card-info")
                t_layout = QVBoxLayout(t_frame)
                t_layout.setSpacing(8)
                
                t_label = QLabel(f"{i+1}. {t.get('description', '')}")
                t_label.setWordWrap(True)
                t_label.setProperty("task_role", "section_header")
                t_layout.addWidget(t_label)
                
                answer_input = QLineEdit()
                answer_input.setPlaceholderText("Введіть відповідь...")
                answer_input.setProperty("type", "tasks")
                t_layout.addWidget(answer_input)
                
                if t.get('hint'):
                    self._add_hidden_hints(t_layout, [t.get('hint', '')])
                
                parent_layout.addWidget(t_frame)
    
    def _create_geometry_widget(self, parent_layout, config):
        """Create geometry visualization widget with matplotlib"""
        import numpy as np
        from matplotlib.patches import Polygon, Circle, Rectangle
        
        geo_frame = QFrame()
        geo_frame.setProperty("task_role", "card")
        geo_layout = QVBoxLayout(geo_frame)
        
        fig = Figure(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#f0f8ff')
        ax = fig.add_subplot(111)
        
        ui_config = config.get("ui_config", {})
        domain = ui_config.get("domain", [0, 12])
        y_range = ui_config.get("range", [0, 10])
        
        shapes = config.get("shapes", [])
        for shape in shapes:
            shape_type = shape.get("type", "")
            color = shape.get("color", "#3498db")
            label = shape.get("label", "")
            
            if shape_type == "rectangle" or shape_type == "triangle":
                points = shape.get("points", [])
                if points:
                    polygon = Polygon(points, closed=True, facecolor=color, edgecolor='black', alpha=0.6, linewidth=2)
                    ax.add_patch(polygon)
                    centroid_x = sum(p[0] for p in points) / len(points)
                    centroid_y = sum(p[1] for p in points) / len(points)
                    ax.annotate(label, (centroid_x, centroid_y), ha='center', va='center', fontsize=9, fontweight='bold')
            
            elif shape_type == "circle":
                center = shape.get("center", [0, 0])
                radius = shape.get("radius", 1)
                circle = Circle(center, radius, facecolor=color, edgecolor='black', alpha=0.6, linewidth=2)
                ax.add_patch(circle)
                ax.annotate(label, center, ha='center', va='center', fontsize=9, fontweight='bold')
        
        ax.set_xlim(domain)
        ax.set_ylim(y_range)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        
        if ui_config.get("show_axes", True):
            ax.axhline(y=0, color='k', linewidth=0.8)
            ax.axvline(x=0, color='k', linewidth=0.8)
        
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(500, 350)
        geo_layout.addWidget(canvas)
        
        parent_layout.addWidget(geo_frame)
        
        tasks = config.get("tasks", [])
        if tasks:
            tasks_label = QLabel("Завдання:")
            tasks_label.setProperty("task_role", "section_header")
            parent_layout.addWidget(tasks_label)
            
            for i, t in enumerate(tasks):
                t_frame = QFrame()
                t_frame.setProperty("task_role", "card-info")
                t_layout = QVBoxLayout(t_frame)
                t_layout.setSpacing(8)
                
                t_label = QLabel(f"{i+1}. {t.get('description', '')}")
                t_label.setWordWrap(True)
                t_label.setProperty("task_role", "section_header")
                t_layout.addWidget(t_label)
                
                answer_input = QLineEdit()
                answer_input.setPlaceholderText("Введіть відповідь...")
                answer_input.setProperty("type", "tasks")
                t_layout.addWidget(answer_input)
                
                if t.get('hint'):
                    self._add_hidden_hints(t_layout, [t.get('hint', '')])
                
                parent_layout.addWidget(t_frame)


    def open_fortune_wheel(self):
        self.wheel = FortuneWheel()
        self.wheel.show()

    def format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.setText(self.format_time(self.time_left))

            if self.time_left < 10:
                self.timer_label.setStyleSheet("color: red; font-weight: bold; font-size: 26px;")
            elif self.time_left < 20:
                self.timer_label.setStyleSheet("color: orange; font-size: 26px;")
            else:
                self.timer_label.setStyleSheet("color: green; font-size: 26px;")
        else:
            if not self.time_up_shown:
                self.time_up_shown = True
                self.timer.stop()
                QMessageBox.warning(self, "Час вийшов", "Час на виконання завдань закінчився!")

    def _add_hidden_hints(self, parent_layout, hints):
        """Add hidden hints widget to a layout"""
        if not hints:
            return
            
        hints_container = QWidget()
        hints_layout = QVBoxLayout(hints_container)
        hints_layout.setContentsMargins(0, 0, 0, 0)
        hints_layout.setSpacing(5)
        
        hints_text = QLabel("••••••••••••••••••••••••••••••")
        hints_text.setProperty("task_role", "hint_label")
        hints_text.setProperty("hint_state", "hidden")
        hints_text.setWordWrap(True)
        hints_text.setProperty("hidden_text", ", ".join(hints) if isinstance(hints, list) else hints)
        
        show_hints_btn = QPushButton("👁 Показати підказки")
        show_hints_btn.setFixedWidth(160)
        show_hints_btn.setProperty("task_role", "hint_button")
        show_hints_btn.setCheckable(True)
        show_hints_btn.clicked.connect(lambda checked, lbl=hints_text, btn=show_hints_btn: self._toggle_hints(checked, lbl, btn))
        
        hints_header = QHBoxLayout()
        hint_title = QLabel("Підказки:")
        hint_title.setProperty("task_role", "hint_title")
        hints_header.addWidget(hint_title)
        hints_header.addWidget(show_hints_btn)
        hints_header.addStretch()
        
        hints_layout.addLayout(hints_header)
        hints_layout.addWidget(hints_text)
        parent_layout.addWidget(hints_container)

    def _toggle_hints(self, checked, hints_label, button):
        """Toggle visibility of hints"""
        if checked:
            hints_label.setText("Підказки: " + hints_label.property("hidden_text"))
            hints_label.setProperty("hint_state", "revealed")
            button.setText("👁 Сховати підказки")
        else:
            hints_label.setText("••••••••••••••••••••••••••••••")
            hints_label.setProperty("hint_state", "hidden")
            button.setText("👁 Показати підказки")

    def _finish_exercises(self):
        """Handle finish button click - check all exercises and show result summary."""
        total_questions = len(self.question_states)

        correct_answers = 0
        answered = 0

        def _norm(v: str) -> str:
            return (v or "").strip().lower()

        for qid, state in self.question_states.items():
            if not state.get("answered"):
                continue
            answered += 1
            is_correct = False
            score = 0.0

            expected = None

            for q in self.lesson_content.get("input_questions", []):
                if q.get("id") == qid:
                    expected = q.get("answer")
                    break

            if expected is None:
                for q in self.lesson_content.get("blank_questions", []):
                    if q.get("id") == qid:
                        expected = q.get("answer")
                        break

            user_val = self.user_answers.get(qid, "")
            if expected is not None:
                is_correct = _norm(str(user_val)) == _norm(str(expected))
                score = 1.0 if is_correct else 0.0
            else:
                is_correct = True
                score = 1.0

            self.question_states[qid]["correct"] = is_correct
            self.question_states[qid]["score"] = score

            if is_correct:
                correct_answers += 1

        if total_questions > 0:
            percentage = int(round((correct_answers / total_questions) * 100))
            result_text = (
                f"Відповідей: {answered} з {total_questions}\n"
                f"Правильних: {correct_answers} з {total_questions}\n"
                f"Результат: {percentage}%"
            )
        else:
            result_text = "Поки що немає автоматично перевірюваних запитань."

        QMessageBox.information(
            self,
            "Результат тесту",
            f"✅ Ваші відповіді збережено.\n\n{result_text}"
        )

        percentage = int(round((correct_answers / total_questions) * 100)) if total_questions > 0 else 0

        import time
        time_spent_minutes = 0
        if self._start_time:
            elapsed_seconds = time.time() - self._start_time
            time_spent_minutes = int(elapsed_seconds // 60)
            logger.info(f"Lesson took {elapsed_seconds:.1f} seconds ({time_spent_minutes} minutes)")

        try:
            if self.user_id and self.lesson_id and self.course_id:
                logger.debug(
                    "Saving lesson completion: user=%s, lesson=%s, course=%s, score=%s%%, time=%d min",
                    self.user_id, self.lesson_id, self.course_id, percentage, time_spent_minutes,
                )
                result = self._progress_service.complete_lesson(
                    user_id=self.user_id,
                    lesson_id=self.lesson_id,
                    course_id=self.course_id,
                    score=percentage,
                    time_spent=time_spent_minutes,
                )
                
                if result:
                    logger.info(f"Lesson completed with score {percentage}%")
                    self.lesson_completed.emit(correct_answers, total_questions, percentage)
                    if self.progress_callback:
                        try:
                            self.progress_callback(
                                lesson_completed=True,
                                percentage=100,
                                answered=total_questions,
                                total=total_questions,
                                correct=correct_answers,
                                correct_percentage=percentage,
                            )
                        except Exception as e:
                            logger.exception("Error calling progress callback after completion")
                else:
                    logger.warning("Failed to save lesson completion")
            else:
                logger.warning("Cannot save lesson – missing user_id, lesson_id, or course_id")
        except Exception as e:
            logger.exception("Error saving lesson completion")

    def _check_code_answer(self, code_box, question):
        """Check the code answer"""
        user_code = code_box.toPlainText().strip()
        expected_code = question.get('code', '').strip()
        
        if not user_code:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть ваш код!")
            return
        
        user_normalized = ''.join(user_code.split()).lower()
        expected_normalized = ''.join(expected_code.split()).lower()
        
        if user_normalized == expected_normalized or expected_code == "":
            QMessageBox.information(self, "Результат", "✅ Правильно! Молодець!")
            code_box.setStyleSheet("""
                QTextEdit { 
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace; 
                    font-size: 13px;
                    background-color: #1e3a1e; 
                    color: #90EE90; 
                    padding: 12px; 
                    border-radius: 6px;
                    border: 2px solid #28a745;
                }
            """)
        else:
            QMessageBox.warning(self, "Результат", "❌ Неправильно. Спробуйте ще раз!")
            code_box.setStyleSheet("""
                QTextEdit { 
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace; 
                    font-size: 13px;
                    background-color: #3a1e1e; 
                    color: #FFB6C1; 
                    padding: 12px; 
                    border-radius: 6px;
                    border: 2px solid #dc3545;
                }
            """)
