class RateCodeError(Exception):
    """Custom exception for rate code errors."""
    pass


class PlayerNotIntError(Exception):
    """Custom exception for non-integer player ID errors."""
    pass


class PlayerNotExistsError(Exception):
    """Custom exception for non-existent player errors."""
    pass


class SelfRatingError(Exception):
    """Custom exception for self-rating attempts."""
    pass


class ParticipationError(Exception):
    """Custom exception for participation validation errors."""
    pass


class DuplicateVoteError(Exception):
    """Custom exception for duplicate vote attempts."""
    pass


class RatingLimitError(Exception):
    """Custom exception for rating limit exceeded."""
    pass


class  InvalidRatingError(Exception):
    """Custom exception for invalid rating values."""
    pass
