from datetime import timedelta

from django.utils import timezone

from apps.players.constants import PlayerIntEnums
from apps.players.exceptions import InvalidRatingError
from apps.players.models import Player, PlayerRating, PlayerRatingVote


class GradeSystem:
    """
    GradeSystem manages player grade levels and rating logic.

    Concepts:
    - Grade: LIGHT (L), MEDIUM (M), HARD (H), PRO (P)
    - Level: 1, 2, 3 (within each grade)
    - Code: string like 'L:1' for Light grade, level 1
    - Rating coefficients: depend on rater and rated grades
    - Level change: UP, DOWN, CONFIRM
    - Methods for updating player ratings based on votes and inactivity
    - Utility methods for retrieving grade objects by code, grade, or level
    - Handles mass rating updates and inactivity downgrades

    Example:
        obj = GradeSystem('L:1')
        next_obj = obj.next
        prev_obj = obj.prev
        coefficient = GradeSystem.get_rating_coefficient('LIGHT', 'MEDIUM')
        value = GradeSystem.get_value(rater, rated, GradeSystem.UP)
    """

    PLAYER_LEVEL_GRADE_CODES: tuple[str, ...] = (
        'L:1',
        'L:2',
        'L:3',
        'M:1',
        'M:2',
        'M:3',
        'H:1',
        'H:2',
        'H:3',
        'P:1',
        'P:2',
        'P:3',
    )

    RATING_COEFFICIENTS: dict[str, dict[str, float]] = {
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

    _objs: list = []
    _map: dict = {}
    _list: list = []

    def __init__(self, code: str):
        self.next = None
        self.prev = None
        self.code = code.upper()

        grade_code, level_str = code.split(':')
        level = int(level_str)
        self.grade = self.GRADES[grade_code]
        self.level = level

    def get_level_grade(self) -> tuple[int, str]:
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
        cls, evaluator_level: str, rated_level: str
    ) -> float:
        """
        Returns the coefficient based on rater and rated player levels.
        """
        return cls.RATING_COEFFICIENTS.get(evaluator_level, {}).get(
            rated_level, 0
        )

    @classmethod
    def get_obj_by_level_grade(cls, grade: str, level: int):
        """
        Returns the GradeSystem object by grade and level.
        """
        return cls.get_by_code(f'{grade[0]}:{level}')

    @classmethod
    def get_value(
        cls, rater: Player, rated: Player, level_change: str
    ) -> float:
        """
        Returns the rating value for player based on level change.
        level_change can be UP, DOWN or CONFIRM.
        If CONFIRM, returns 0.
        """

        if level_change == cls.CONFIRM:
            return 0
        coefficient = cls.get_rating_coefficient(
            evaluator_level=rater.rating.grade, rated_level=rated.rating.grade
        )
        if level_change == cls.UP:
            return 1 * coefficient
        if level_change == cls.DOWN:
            return -1 * coefficient
        raise InvalidRatingError(
            f'Invalid level_change value: {level_change}.'
        )

    @classmethod
    def update_player_rating(
        cls, player: Player, vote: PlayerRatingVote
    ) -> str:
        """
        Updates a single player's rating based on their votes.
        Returns the type of change:
            'unchanged', 'updated', 'upgraded', 'downgraded'
        """
        player_rating: PlayerRating = player.rating
        if vote.value == 0:
            vote.is_counted = True
            vote.save()
            return 'unchanged'
        rating_value_sum = player_rating.value + vote.value
        new_grade = player_rating.grade
        new_level = player_rating.level_mark
        new_value = rating_value_sum
        result = 'updated'
        if rating_value_sum > PlayerIntEnums.MAX_RATING_VALUE:
            change: GradeSystem = cls.get_obj_by_level_grade(
                player_rating.grade, player_rating.level_mark
            ).next
            if change:
                new_grade = change.grade
                new_level = change.level
                new_value = PlayerIntEnums.MIN_RATING_VALUE
                result = 'upgraded'
            else:
                new_value = PlayerIntEnums.MAX_RATING_VALUE
                result = 'updated'
        elif rating_value_sum < PlayerIntEnums.MIN_RATING_VALUE:
            change = cls.get_obj_by_level_grade(
                player_rating.grade, player_rating.level_mark
            ).prev
            if change:
                new_grade = change.grade
                new_level = change.level
                new_value = PlayerIntEnums.MAX_RATING_VALUE
                result = 'downgraded'
            else:
                new_value = PlayerIntEnums.MIN_RATING_VALUE
                result = 'updated'
        player_rating.grade = new_grade
        player_rating.level_mark = new_level
        player_rating.value = new_value
        player_rating.save()
        vote.is_counted = True
        vote.save()
        return result

    @classmethod
    def downgrade_inactive_players(
        cls, days: int = PlayerIntEnums.PLAYER_INACTIVE_DAYS
    ) -> int:
        """
        Downgrade player level by one step inside current grade if no activity
        for `days`. Grade (Pro, Hard, etc.) does not change, only level_mark
        decreases. Returns the number of downgraded players.
        If level_mark is already 1, it stays at 1.
        A player is considered inactive if they have not participated in any
        games in the last `60` days.
        A player's rating value is reset to 6 upon downgrade or upgrade.
        """

        inactive_ratings = PlayerRating.objects.filter(
            updated_at__lt=timezone.now() - timedelta(days=days)
        ).select_related('player')
        downgraded_count = 0
        for rating in inactive_ratings:
            player: Player = rating.player
            if player.was_active_recently(days=days):
                continue
            if rating.level_mark > 1:
                rating.level_mark = rating.level_mark - 1
                rating.value = PlayerIntEnums.DEFAULT_RATING
                rating.save()
                downgraded_count += 1
        return downgraded_count


GradeSystem.setup()
