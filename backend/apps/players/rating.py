from apps.players.models import Player, PlayerRating, PlayerRatingVote


class PlayerLevelGrade:
    """
    Represents a player's level and grade node for a doubly linked list.
    """

    PLAYER_LEVEL_GRADE_CODES: tuple[str] = (
        'L:1', 'L:2', 'L:3',
        'M:1', 'M:2', 'M:3',
        'H:1', 'H:2', 'H:3',
        'P:1', 'P:2', 'P:3'
    )

    RATING_COEFFICIENTS: dict[dict[str:float]] = {
        'LIGHT': {'LIGHT': 0.5, 'MEDIUM': 0.5, 'HARD': 0, 'PRO': 0},
        'MEDIUM': {'LIGHT': 1.0, 'MEDIUM': 1.0, 'HARD': 0.5, 'PRO': 0},
        'HARD': {'LIGHT': 2.0, 'MEDIUM': 2.0, 'HARD': 1.0, 'PRO': 0.5},
        'PRO': {'LIGHT': 3.0, 'MEDIUM': 3.0, 'HARD': 2.0, 'PRO': 1.0},
    }

    GRADES = {
        'L': 'LIGHT',
        'M': 'MEDIUM',
        'H': 'HARD',
        'P': 'PRO',
    }

    UP: str = 'UP'
    DOWN: str = 'DOWN'
    CONFIRM: str = 'CONFIRM'

    _objs = []
    _map = {}
    _list = []

    def __init__(self, code: str):
        self.next = None
        self.prev = None
        self.code = code
        self.grade, self.level = code.split(':')
        self.grade = self.GRADES[self.grade]
        self.level = int(self.level)

    def get_level_grade(self) -> tuple[str, int]:
        return self.level, self.grade

    @classmethod
    def setup(cls):
        cls._objs = [cls(code) for code in cls.PLAYER_LEVEL_GRADE_CODES]
        for i, obj in enumerate(cls._objs):
            if i > 0:
                obj.prev = cls._objs[i - 1]
            if i < len(cls._objs) - 1:
                obj.next = cls._objs[i + 1]
        cls._map = {obj.code: obj for obj in cls._objs}
        cls._list = cls._objs

    @classmethod
    def get_by_code(cls, code: str):
        return cls._map.get(code)

    @classmethod
    def all(cls):
        return cls._list

    @classmethod
    def get_rating_coefficient(
        cls,
        evaluator_level: str,
        rated_level: str
        ) -> float:
        """Returns the coefficient based on rater and rated player levels."""
        return cls.RATING_COEFFICIENTS.get(
            evaluator_level,
            {}
        ).get(rated_level, 0)

    @classmethod
    def get_obj_by_level_grade(cls, grade: str, level: int):
        """
        Returns the PlayerLevelGrade object by grade and level.
        """
        return cls.get_by_code(f'{grade[0]}:{level}')

    @classmethod
    def get_value(
        cls,
        rater: Player,
        rated: Player,
        level_change: str
        ) -> int:
        """
        Returns the rating value for player based on level change.
        level_change can be UP, DOWN or CONFIRM.
        If CONFIRM, returns 0.
        """
        if level_change == cls.CONFIRM:
            return 0
        coefficient = cls.get_rating_coefficient(
            evaluator_level=rater.rating.grade,
            rated_level=rated.rating.grade
        )
        if level_change == cls.UP:
            return int(1 * coefficient)
        elif level_change == cls.DOWN:
            return int(-1 * coefficient)
        return 0

    @classmethod
    def update_players_rating(cls):
        """Updates player ratings based on votes."""
        players = Player.objects.all()
        for player in players:
            player_rating: PlayerRating = player.rating
            last_day_rates = PlayerRatingVote.objects.filter(
                rated_player=player,
                is_counted=False
            )
            votes = list(last_day_rates)
            rating_value_sum = sum(
                v.rating for v in votes
            ) + player_rating.value
            new_grade = player_rating.grade
            new_level = player_rating.level_mark
            new_value = player_rating.value

            if rating_value_sum < 0:
                change = cls.get_obj_by_level_grade(
                    player_rating.grade,
                    player_rating.level_mark
                ).prev
                if change:
                    new_grade = change.grade
                    new_level = change.level
                    new_value = 6
            elif rating_value_sum > 12:
                change = cls.get_obj_by_level_grade(
                    player_rating.grade,
                    player_rating.level_mark
                ).next
                if change:
                    new_grade = change.grade
                    new_level = change.level
                    new_value = 6
                else:
                    new_value = rating_value_sum
            else:
                new_value = rating_value_sum
            PlayerRating.objects.filter(pk=player_rating.pk).update(
                grade=new_grade,
                level_mark=new_level,
                value=new_value
            )
            last_day_rates.update(is_counted=True)
