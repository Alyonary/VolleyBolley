import random
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.event.models import Game
from apps.players.models import Player, PlayerRating, PlayerRatingVote, User
from apps.players.rating import GradeSystem


@pytest.mark.django_db
class TestGradeSystem:
    
    def setup_method(self):
        """Initialize before each test."""
        GradeSystem.setup()
    
    def test_grade_system_initialization(self):
        """Test grade system initialization."""
        assert len(GradeSystem._objs) == 12
        assert len(GradeSystem._map) == 12
        assert len(GradeSystem._list) == 12
        
        expected_codes = [
            'L:1', 'L:2', 'L:3',
            'M:1', 'M:2', 'M:3', 
            'H:1', 'H:2', 'H:3',
            'P:1', 'P:2', 'P:3'
        ]
        actual_codes = [obj.code for obj in GradeSystem._objs]
        assert actual_codes == expected_codes
    
    def test_grade_system_next_prev_links(self):
        """Test next and previous links between grade levels."""
        for i, obj in enumerate(GradeSystem._objs):
            if i == 0:
                assert obj.prev is None
                assert obj.next == GradeSystem._objs[i + 1]
            elif i == len(GradeSystem._objs) - 1:
                assert obj.next is None
                assert obj.prev == GradeSystem._objs[i - 1]
            else:
                assert obj.prev == GradeSystem._objs[i - 1]
                assert obj.next == GradeSystem._objs[i + 1]

    def test_order_of_levels(self):
        """Test correct order of grades and levels."""
        expected_order = [
            ('L', 1), ('L', 2), ('L', 3),
            ('M', 1), ('M', 2), ('M', 3),
            ('H', 1), ('H', 2), ('H', 3),
            ('P', 1), ('P', 2), ('P', 3)
        ]
        
        for i, (grade_code, level) in enumerate(expected_order):
            obj = GradeSystem._objs[i]
            expected_grade = GradeSystem.GRADES[grade_code]
            
            assert obj.grade == expected_grade
            assert obj.level == level
            assert obj.code == f'{grade_code}:{level}'
            
            if i > 0:
                prev_obj = GradeSystem._objs[i - 1]
                assert obj.prev == prev_obj
            else:
                assert obj.prev is None
                
            if i < len(expected_order) - 1:
                next_obj = GradeSystem._objs[i + 1]
                assert obj.next == next_obj
            else:
                assert obj.next is None

    def test_grade_system_object_creation(self):
        """Test GradeSystem object creation."""
        obj = GradeSystem('L:2')
        
        assert obj.code == 'L:2'
        assert obj.grade == 'LIGHT'
        assert obj.level == 2
    
    def test_grade_system_navigation(self):
        """Test navigation between levels."""
        obj = GradeSystem.get_by_code('M:2')
        assert obj.prev.code == 'M:1'
        assert obj.next.code == 'M:3'
        
        first_obj = GradeSystem.get_by_code('L:1')
        assert first_obj.prev is None
        assert first_obj.next.code == 'L:2'
        
        last_obj = GradeSystem.get_by_code('P:3')
        assert last_obj.next is None
        assert last_obj.prev.code == 'P:2'
    
    def test_get_by_code(self):
        """Test getting object by code."""
        obj = GradeSystem.get_by_code('H:3')
        assert obj is not None
        assert obj.code == 'H:3'
        assert obj.grade == 'HARD'
        assert obj.level == 3
        
        invalid_obj = GradeSystem.get_by_code('X:1')
        assert invalid_obj is None
    
    def test_get_level_grade(self):
        """Test getting level and grade."""
        obj = GradeSystem('P:1')
        level, grade = obj.get_level_grade()
        assert level == 1
        assert grade == 'PRO'
    
    def test_get_rating_coefficient(self):
        """Test getting rating coefficients."""
        assert GradeSystem.get_rating_coefficient('LIGHT', 'LIGHT') == 0.5
        assert GradeSystem.get_rating_coefficient('MEDIUM', 'LIGHT') == 1.0
        assert GradeSystem.get_rating_coefficient('HARD', 'MEDIUM') == 2.0
        assert GradeSystem.get_rating_coefficient('PRO', 'HARD') == 2.0
        
        assert GradeSystem.get_rating_coefficient('INVALID', 'LIGHT') == 0
        assert GradeSystem.get_rating_coefficient('LIGHT', 'INVALID') == 0
    
    def test_get_obj_by_level_grade(self):
        """Test getting object by grade and level."""
        obj = GradeSystem.get_obj_by_level_grade('MEDIUM', 2)
        assert obj.code == 'M:2'
        assert obj.grade == 'MEDIUM'
        assert obj.level == 2
        
        obj_pro = GradeSystem.get_obj_by_level_grade('PRO', 1)
        assert obj_pro.code == 'P:1'
        assert obj_pro.grade == 'PRO'
        assert obj_pro.level == 1
    
    def test_get_value_confirm(self, players):
        """Test getting value for CONFIRM."""
        rater = players['player1']
        rated = players['player2']
        
        value = GradeSystem.get_value(rater, rated, GradeSystem.CONFIRM)
        assert value == 0
    
    def test_get_value_up_and_down(self, players):
        """Test getting value for UP and DOWN."""
        rater = players['player1']
        rater.rating.grade = 'MEDIUM'
        rated = players['player2']
        rated.rating.grade = 'LIGHT'
        value_up = GradeSystem.get_value(rater, rated, GradeSystem.UP)
        assert value_up == 1
        value_down = GradeSystem.get_value(rater, rated, GradeSystem.DOWN)
        assert value_down == -1
        rater.rating.grade = 'LIGHT'
        rated.rating.grade = 'LIGHT'
        value_up_half = GradeSystem.get_value(rater, rated, GradeSystem.UP)
        assert value_up_half == 0.5
    
    def test_all_method(self):
        """Test getting all objects."""
        all_objs = GradeSystem.all()
        assert len(all_objs) == 12
        assert all_objs[0].code == 'L:1'
        assert all_objs[-1].code == 'P:3'


@pytest.mark.django_db
class TestGradeSystemDatabaseOperations:
    
    def test_player_rating_object_creation(self):
        """Test PlayerRating object creation."""
        user = User.objects.create(
            username='r_test_user',
            email='r_test@mail,com',
            password='testpass123'
        )
        player = Player.objects.create(user=user)
        player.refresh_from_db()
        assert hasattr(player, 'rating')
        assert isinstance(player.rating, PlayerRating)
        assert player.rating.value == 6
        assert player.rating.grade == 'LIGHT'
        assert player.rating.level_mark == 2
        assert player.rating.updated_at is not None

    def test_player_start_rating(self, players):
        """Test initial player rating creation."""
        player: Player = random.choice(list(players.values()))
        player.refresh_from_db()
        assert player.rating is not None
        assert player.rating.value == 6
        assert player.rating.level_mark == 2

    def test_update_players_rating_no_votes(
        self,
        player_thailand
    ):
        """Test rating update without votes."""
        initial_rating = player_thailand.rating.value
        stats = GradeSystem.update_players_rating()
        player_thailand.refresh_from_db()
        assert player_thailand.rating.value == initial_rating
        assert stats['unchanged'] >= 1
    
    def test_update_players_rating_with_votes(
        self,
        players
    ):
        """Test rating update with votes."""
        player1, player2 = players['player1'], players['player2']
        initial_value = player1.rating.value
        
        PlayerRatingVote.objects.create(
            rater=player2,
            rated=player1,
            value=2,
            is_counted=False
        )
        PlayerRatingVote.objects.create(
            rater=player2,
            rated=player1,
            value=3,
            is_counted=False
        )
        
        stats = GradeSystem.update_players_rating()
        assert stats['updated'] == 1
        player1.refresh_from_db()
        expected_value = initial_value + 2 + 3
        assert player1.rating.value == expected_value
        
        assert PlayerRatingVote.objects.filter(
            rated=player1,
            is_counted=True
        ).count() == 2
    
    def test_update_players_rating_upgrade(
        self,
        players
    ):
        """Test player level upgrade."""
        player1 = players['player1']
        player1.rating.value = 10
        player1.rating.grade = 'LIGHT'
        player1.rating.level_mark = 3
        player1.rating.save()
        
        raters = players.copy()
        raters.pop('player1')
        for rater in raters.values():
            rater.rating.grade = 'MEDIUM'
            rater.rating.save()
            PlayerRatingVote.objects.create(
                rater=rater,
                rated=player1,
                value=1,
                is_counted=False
            )
        
        stats = GradeSystem.update_players_rating()
        player1.refresh_from_db()
        assert player1.rating.grade == 'MEDIUM'
        assert player1.rating.level_mark == 1
        assert player1.rating.value == 6
        assert stats['upgraded'] == 1
        update_with_old_votes_stats = GradeSystem.update_players_rating()
        player1.refresh_from_db()
        assert player1.rating.level_mark == 1
        assert player1.rating.value == 6
        assert update_with_old_votes_stats['unchanged'] >= 1
    
    def test_update_players_rating_downgrade(
        self,
        players
    ):
        """Test player level downgrade."""
        player1 = players['player1']
        player1.rating.value = 6
        player1.rating.grade = 'MEDIUM'
        player1.rating.level_mark = 1
        player1.rating.save()
        raters = players.copy()
        raters.pop('player1')
        for rater in raters.values():
            rater.rating.grade = 'PRO'
            PlayerRatingVote.objects.create(
                rater=rater,
                rated=player1,
                value=GradeSystem.get_value(
                    rater=rater,
                    rated=player1,
                    level_change=GradeSystem.DOWN
                ),
                is_counted=False
            )
        stats = GradeSystem.update_players_rating()
        player1.refresh_from_db()
        assert player1.rating.level_mark == 3
        assert player1.rating.value == 6
        assert player1.rating.grade == 'LIGHT'
        assert stats['downgraded'] >= 1
        update_with_old_votes_stats = GradeSystem.update_players_rating()
        player1.refresh_from_db()
        assert player1.rating.level_mark == 3
        assert player1.rating.value == 6
        assert update_with_old_votes_stats['unchanged'] >= 1
    
    def test_update_players_rating_no_downgrade_at_minimum(
        self,
        player_thailand
    ):
        """Test no downgrade below L:1 level."""
        player_thailand.rating.value = 1
        player_thailand.rating.grade = 'LIGHT'
        player_thailand.rating.level_mark = 1
        player_thailand.rating.save()
        
        PlayerRatingVote.objects.create(
            rater=player_thailand,
            rated=player_thailand,
            value=-3,
            is_counted=False
        )
        stats = GradeSystem.update_players_rating()
        player_thailand.refresh_from_db()
        assert player_thailand.rating.grade == 'LIGHT'
        assert player_thailand.rating.level_mark == 1
        assert player_thailand.rating.value == 1
        assert stats['unchanged'] >= 1
    

    def test_downgrade_inactive_players(
        self,
        players
    ):
        """Test downgrading inactive players."""
        player = players['player5']
        old_date = timezone.now() - timedelta(days=70)
        Game.objects.filter(players=player).delete()
        player.rating.value = 10
        player.rating.grade = 'MEDIUM'
        player.rating.level_mark = 3
        player.rating.save()
        PlayerRating.objects.filter(id=player.rating.id).update(
            updated_at=old_date
        )
        player.refresh_from_db()
        
        assert not player.was_active_recently(days=60)
        assert player.rating.updated_at < timezone.now() - timedelta(days=60)
        
        downgraded_count = GradeSystem.downgrade_inactive_players()
        player.refresh_from_db()
        
        assert player.rating.level_mark == 2
        assert player.rating.grade == 'MEDIUM'
        assert player.rating.value == 6
        assert downgraded_count >= 1
    
    @patch('apps.players.models.Player.was_active_recently')
    def test_downgrade_inactive_players_minimum_level(
        self,
        mock_was_active,
        players
    ):
        """Test no downgrade below level 1 for inactive players."""
        player = players['player5']
        player.rating.level_mark = 1
        player.rating.save()
        mock_was_active.return_value = False
        old_date = timezone.now() - timedelta(days=70)
        player.rating.updated_at = old_date
        player.rating.level_mark = 1
        player.rating.save()
        GradeSystem.downgrade_inactive_players()
        player.refresh_from_db()
        assert player.rating.level_mark == 1
    
    @patch('apps.players.models.Player.was_active_recently')
    def test_downgrade_inactive_players_active_user(
        self,
        mock_was_active,
        player_thailand
    ):
        """Test active players are not downgraded."""
        mock_was_active.return_value = True
        
        old_date = timezone.now() - timedelta(days=70)
        player_thailand.rating.updated_at = old_date
        initial_level = player_thailand.rating.level_mark
        player_thailand.rating.save()
        
        GradeSystem.downgrade_inactive_players()
        
        player_thailand.refresh_from_db()
        assert player_thailand.rating.level_mark == initial_level


@pytest.mark.django_db
class TestGradeSystemEdgeCases:
    
    def test_invalid_grade_code(self):
        """Test handling invalid grade code."""
        with pytest.raises(ValueError):
            GradeSystem('INVALID:CODE')
    
    def test_invalid_level_in_code(self):
        """Test handling invalid level in code."""
        with pytest.raises(ValueError):
            GradeSystem('L:invalid')
    
    def test_rating_coefficients_coverage(self):
        """Test coverage of all rating coefficients."""
        grades = ['LIGHT', 'MEDIUM', 'HARD', 'PRO']
        
        for evaluator in grades:
            for rated in grades:
                coefficient = GradeSystem.get_rating_coefficient(
                    evaluator, rated
                )
                assert isinstance(coefficient, (int, float))
                assert coefficient >= 0
    
    def test_get_value_invalid_level_change(self):
        """Test handling invalid level change type."""
        rater = MagicMock()
        rated = MagicMock()
        rater.rating.grade = 'LIGHT'
        rated.rating.grade = 'LIGHT'
        
        value = GradeSystem.get_value(rater, rated, 'INVALID_CHANGE')
        assert value == 0
