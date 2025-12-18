"""
Lesson Content Handler - Transforms database content into UI task format
"""
import logging
from typing import Dict, List, Any, Optional
from src.services.lesson_service import LessonService
from src.services.content_service import ContentService
from src.services.course_service import CourseService

logger = logging.getLogger(__name__)


class LessonContentHandler:
    """Handles loading and transforming lesson content from database to UI format"""
    
    def __init__(self):
        self.lesson_service = LessonService()
        self.content_service = ContentService()
        self.course_service = CourseService()
        self.lessons_cache = {}
        self.content_cache = {}
    
    def load_course_lessons(self, course_id: str) -> Dict[str, Any]:
        """
        Load all lessons for a course and return structured data
        
        Returns:
            Dict with 'lessons' list and 'content' dict keyed by lesson title
        """
        try:
            lessons = self.lesson_service.get_lessons_by_course_id(course_id)
            
            lessons_by_title = {}
            lesson_content_data = {}
            lessons_list = []

            course_topic = None
            try:
                course = self.course_service.get_course_by_id(course_id)
                course_topic = getattr(course, "topic", None)
            except Exception:
                course_topic = None
            
            for lesson in lessons:
                lesson_id = str(lesson.id)
                lessons_by_title[lesson.title] = lesson_id
                
                lessons_list.append({
                    'id': lesson_id,
                    'title': lesson.title,
                    'order': lesson.lesson_order,
                    'duration': f"{lesson.estimated_time} хв",
                    'points': lesson.points_reward
                })
                
                content = self._load_lesson_content(lesson_id)
                if not self._is_informatics_course(course_topic):
                    content = self._adapt_for_non_programming_course(content)
                lesson_content_data[lesson.title] = content
                lesson_content_data[lesson_id] = content
            
            self.lessons_cache[course_id] = lessons_by_title
            self.content_cache[course_id] = lesson_content_data
            
            return {
                'lessons': lessons_list,
                'lessons_by_title': lessons_by_title,
                'content': lesson_content_data
            }
            
        except Exception as e:
            logger.exception("Error loading course lessons")
            return {'lessons': [], 'lessons_by_title': {}, 'content': {}}
    
    def _load_lesson_content(self, lesson_id: str) -> Dict[str, Any]:
        """Load and transform content for a single lesson"""
        try:
            contents = self.content_service.get_lesson_content(lesson_id)
            
            lesson_data = self._create_empty_content_structure()
            
            for content in contents:
                self._process_content_item(content, lesson_data)

            return lesson_data
            
        except Exception as e:
            logger.exception("Error loading lesson content for lesson_id=%s", lesson_id)
            return self._create_empty_content_structure()
    
    def _create_empty_content_structure(self) -> Dict[str, Any]:
        """Create empty content structure with all possible fields"""
        return {
            "theory": "",
            "test_questions": [],
            "true_false_questions": [],
            "input_questions": [],
            "blank_questions": [],
            "code_questions": [],
            "fix_error_questions": [],
            "drag_and_drop_questions": [],
            "interactive_tasks": [],
        }

    def _is_informatics_course(self, course_topic) -> bool:
        if course_topic is None:
            return False
        try:
            topic_val = course_topic.value if hasattr(course_topic, "value") else str(course_topic)
        except Exception:
            topic_val = str(course_topic)
        topic_norm = (topic_val or "").strip().lower()
        return (
            topic_norm == "інформатика"
            or topic_norm == "informatics"
            or "інформ" in topic_norm
        )

    def _adapt_for_non_programming_course(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        code_questions = lesson_data.get("code_questions") or []
        fix_error_questions = lesson_data.get("fix_error_questions") or []
        if not code_questions and not fix_error_questions:
            return lesson_data

        input_questions = list(lesson_data.get("input_questions") or [])

        for q in code_questions:
            input_questions.append(
                {
                    "id": q.get("id"),
                    "question": q.get("question", ""),
                    "answer": q.get("code", ""),
                    "hints": q.get("hints", []) or [],
                }
            )

        for q in fix_error_questions:
            input_questions.append(
                {
                    "id": q.get("id"),
                    "question": q.get("question", ""),
                    "answer": q.get("solution", ""),
                    "hints": q.get("hints", []) or [],
                }
            )

        lesson_data["input_questions"] = input_questions
        lesson_data["code_questions"] = []
        lesson_data["fix_error_questions"] = []
        return lesson_data
    
    def _process_content_item(self, content, lesson_data: Dict[str, Any]):
        """Process a single content item and update lesson_data"""
        content_type = content.content_type
        
        if content_type == "theory":
            self._process_theory(content, lesson_data)
        elif content_type == "exercise":
            self._process_exercise(content, lesson_data)
        elif content_type == "assessment":
            self._process_assessment(content, lesson_data)
        elif content_type == "quiz":
            self._process_quiz(content, lesson_data)
        elif content_type == "interactive":
            self._process_interactive(content, lesson_data)
    
    def _process_theory(self, content, lesson_data: Dict[str, Any]):
        """Process theory content"""
        if hasattr(content, 'text_content') and content.text_content:
            lesson_data["theory"] = content.text_content
    
    def _process_exercise(self, content, lesson_data: Dict[str, Any]):
        """Process exercise content"""
        if hasattr(content, 'problem_statement') and content.problem_statement:
            content_id = str(content.id) if hasattr(content, 'id') else str(id(content))
            answer_type = getattr(content, 'answer_type', 'text')
            initial_code = getattr(content, 'initial_code', '') or ''

            if not initial_code and hasattr(content, 'metadata') and isinstance(content.metadata, dict):
                initial_code = content.metadata.get('initial_code', '') or content.metadata.get('buggy_code', '')

            solution_val = content.solution if hasattr(content, 'solution') else ""
            hints_val = content.hints if hasattr(content, 'hints') and content.hints else []

            if answer_type == "fill_blank":
                lesson_data["blank_questions"].append({
                    "id": content_id,
                    "question": content.problem_statement,
                    "answer": solution_val
                })
            elif answer_type == "fix_error" or (initial_code and "виправ" in (content.problem_statement or "").lower()):
                if not initial_code and solution_val:
                    initial_code = solution_val
                lesson_data["fix_error_questions"].append({
                    "id": content_id,
                    "question": content.problem_statement,
                    "code": initial_code,
                    "solution": solution_val,
                    "hints": hints_val,
                })
            elif answer_type == "code" or initial_code:
                lesson_data["code_questions"].append({
                    "id": content_id,
                    "question": content.problem_statement,
                    "code": initial_code,
                    "answer": solution_val,
                    "hints": hints_val,
                })
            else:
                lesson_data["input_questions"].append({
                    "id": content_id,
                    "question": content.problem_statement,
                    "answer": solution_val,
                    "hints": hints_val,
                })
    
    def _process_assessment(self, content, lesson_data: Dict[str, Any]):
        """Process assessment content with multiple question types"""
        if not hasattr(content, 'questions') or not content.questions:
            return

        questions = content.questions
        if isinstance(questions, dict):
            questions = questions.get('questions', [])
        if not isinstance(questions, list):
            return
        
        for q_idx, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            q_type = question.get('type', 'multiple_choice')
            q_id = question.get('id', f"{content.id}_q_{q_idx}" if hasattr(content, 'id') else f"q_{q_idx}")
            
            if q_type == 'multiple_choice':
                correct_idx = question.get('correct_answer', 0)
                options = question.get('options', [])
                if isinstance(correct_idx, int) and correct_idx < len(options):
                    answer = options[correct_idx]
                else:
                    answer = correct_idx
                
                lesson_data["test_questions"].append({
                    "id": q_id,
                    "question": question.get('question', ''),
                    "options": options,
                    "answer": answer
                })
            
            elif q_type == 'true_false':
                lesson_data["true_false_questions"].append({
                    "id": q_id,
                    "question": question.get('question', ''),
                    "answer": question.get('correct_answer', False)
                })
            
            elif q_type == 'short_answer' or q_type == 'input':
                lesson_data["input_questions"].append({
                    "id": q_id,
                    "question": question.get('question', ''),
                    "answer": question.get('correct_answer', '')
                })
            
            elif q_type == 'fill_blank':
                lesson_data["blank_questions"].append({
                    "id": q_id,
                    "question": question.get('question', ''),
                    "question_part2": question.get('question_part2', ''),
                    "answer": question.get('correct_answer', '')
                })
            
            elif q_type == 'drag_drop' or q_type == 'matching':
                lesson_data["drag_and_drop_questions"].append({
                    "id": q_id,
                    "question": question.get('question', ''),
                    "descriptions": question.get('descriptions', []),
                    "words": question.get('words', []),
                    "answers": question.get('answers', [])
                })
    
    def _process_quiz(self, content, lesson_data: Dict[str, Any]):
        """Process quiz content (similar to assessment)"""
        self._process_assessment(content, lesson_data)
    
    def _process_interactive(self, content, lesson_data: Dict[str, Any]):
        """Process interactive content"""
        content_id = str(content.id) if hasattr(content, 'id') else str(id(content))
        interaction_type = getattr(content, 'interaction_type', None)
        interaction_data = getattr(content, 'interaction_data', {})
        if interaction_type is None:
            interaction_type = getattr(content, 'interactive_type', None)
        if interaction_data is None or not isinstance(interaction_data, dict):
            interaction_data = getattr(content, 'configuration', interaction_data)
        if interaction_data is None or not isinstance(interaction_data, dict):
            interaction_data = {}
        instructions = getattr(content, 'instructions', '')
        title = getattr(content, 'title', '')
        
        if interaction_type == 'drag_drop':
            lesson_data["drag_and_drop_questions"].append({
                "id": content_id,
                "question": instructions or interaction_data.get('question', ''),
                "descriptions": interaction_data.get('descriptions', []),
                "words": interaction_data.get('words', []),
                "answers": interaction_data.get('answers', [])
            })
        
        elif interaction_type == 'code_editor':
            lesson_data["code_questions"].append({
                "id": content_id,
                "question": instructions or interaction_data.get('question', ''),
                "snippets": interaction_data.get('snippets', []),
                "required": interaction_data.get('required', [])
            })
        
        elif interaction_type == 'fix_error':
            code_snippet = (
                interaction_data.get('code')
                or interaction_data.get('initial_code')
                or interaction_data.get('buggy_code')
                or interaction_data.get('solution')
                or ''
            )
            lesson_data["fix_error_questions"].append({
                "id": content_id,
                "question": instructions or interaction_data.get('question', ''),
                "code": code_snippet,
                "fixes": interaction_data.get('fixes', []),
                "solution": interaction_data.get('solution', '')
            })
        
        elif interaction_type in ['tool', 'simulation', 'visualization']:
            interactive_task = {
                "id": content_id,
                "type": interaction_type,
                "title": title,
                "instructions": instructions,
                "configuration": interaction_data
            }
            lesson_data["interactive_tasks"].append(interactive_task)
    
    def find_course_for_lesson(self, lesson_name: str) -> Optional[str]:
        """Find which course contains a lesson by name"""
        try:
            courses = self.course_service.get_all_courses()
            
            for course in courses:
                lessons = self.lesson_service.get_lessons_by_course_id(str(course.id))
                lesson_titles = [lesson.title for lesson in lessons]
                
                if lesson_name in lesson_titles:
                    return str(course.id)
            
            return None
            
        except Exception as e:
            logger.exception("Error finding course for lesson")
            return None
    
    def get_lesson_content(self, course_id: str, lesson_title: str) -> Dict[str, Any]:
        """Get content for a specific lesson, loading if necessary"""
        if course_id not in self.content_cache:
            self.load_course_lessons(course_id)
        
        content = self.content_cache.get(course_id, {}).get(lesson_title)
        
        if content:
            return content
        
        return self._create_default_content(lesson_title)
    
    def _create_default_content(self, lesson_title: str) -> Dict[str, Any]:
        """Create default content when no real content is available"""
        return {
            "theory": f"Теоретичний матеріал для уроку: {lesson_title}\n\nКонтент буде додано незабаром.",
            "test_questions": [],
            "true_false_questions": [],
            "input_questions": [],
            "blank_questions": [],
            "code_questions": [],
            "fix_error_questions": [],
            "drag_and_drop_questions": [],
        }
