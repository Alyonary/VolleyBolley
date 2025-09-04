PLAYER_LEVEL_GRADE_CODES: tuple[str] = (
    'L:1', 'L:2', 'L:3',
    'M:1', 'M:2', 'M:3',
    'H:1', 'H:2', 'H:3',
    'P:1', 'P:2', 'P:3'
)

RATING_COEFFICIENTS = {
    'LIGHT': {'LIGHT': 0.5, 'MEDIUM': 0.5, 'HARD': 0, 'PRO': 0},
    'MEDIUM': {'LIGHT': 1.0, 'MEDIUM': 1.0, 'HARD': 0.5, 'PRO': 0},
    'HARD': {'LIGHT': 2.0, 'MEDIUM': 2.0, 'HARD': 1.0, 'PRO': 0.5},
    'PRO': {'LIGHT': 3.0, 'MEDIUM': 3.0, 'HARD': 2.0, 'PRO': 1.0},
}

LEVEL_UP: str = 'UP'
LEVEL_DOWN: str = 'DOWN'

class PlayerLevelChange:
    """
    Enum-like class for player level change actions.

    UP: 1
    CONFIRM: 0
    DOWN: -1
    """
    UP = 1
    CONFIRM = 0
    DOWN = -1


class PlayerLevelGrade:
    """
    Represents a player's level and grade node for a doubly linked list.

    Each node contains a code (e.g., 'L:1'), level (e.g., 'LIGHT'), and grade.
    Nodes are linked to previous and next nodes for easy navigation.
    """

    def __init__(self, code: str):
        self.next = None
        self.prev = None
        self.code = code
        self.level, self.grade = code.split(':')
        self.grade = int(self.grade)

    def get_level_grade(self) -> tuple[str, int]:
        """
        Returns the level and grade as a tuple.

        :return: (level, grade)
        """
        return self.level, self.grade

_player_level_grade_objs = [
    PlayerLevelGrade(code) for code in PLAYER_LEVEL_GRADE_CODES
]

for i, obj in enumerate(_player_level_grade_objs):
    if i > 0:
        obj.prev = _player_level_grade_objs[i - 1]
    if i < len(_player_level_grade_objs) - 1:
        obj.next = _player_level_grade_objs[i + 1]

PLAYER_LEVEL_GRADE_MAP = {
    obj.code: obj for obj in _player_level_grade_objs
}
PLAYER_LEVEL_GRADE_LIST = _player_level_grade_objs

def get_level_grade(code: str) -> PlayerLevelGrade:
    """
    Returns the PlayerLevelGrade object by code.

    :param code: Level-grade code (e.g., 'L:1')
    :return: PlayerLevelGrade object
    """
    return PLAYER_LEVEL_GRADE_MAP.get(code)

def get_rating_coefficient(evaluator_level: str, rated_level: str) -> float:
    """
    Returns the rating coefficient based on evaluator and rated levels.

    :param playerevaluator_level_level: Evaluator's level (e.g., 'LIGHT')
    :param rated_level: Rated player's level (e.g., 'PRO')
    :return: Coefficient as float
    """
    return RATING_COEFFICIENTS.get(evaluator_level, {}).get(rated_level, 0)
