class EventValidationMessages:
    """Class containing validation messages for event app."""

    CURRENCY_NOT_FOUND = 'Currency for country {country} not found.'
    NO_PAYMENT_ACCOUNT = 'No payment account found for this payment type'
    NOT_DEFINED = 'Not defined'
    PLAYERS_NUMBER_RANGE = (
        'Number of players must be between {minimal} and {maximal}!'
    )
    GAME_START_FUTURE = 'Game start time can be in future.'
    END_TIME_AFTER_START = (
        'The end time of the game must be later than the start time.'
    )
    TIMEZONE_REQUIRED = 'Time must include timezone information'
    INVITE_SELF = 'You cannot invite yourself.'
    PLAYERS_UNIQUE = 'The players should not repeat themselves.'
    INVITATION_EXISTS = 'This invitation already exists!'
    NO_REGISTERED_PLAYERS = (
        'Cannot invite players to the event without any registered players.'
    )
    PLAYER_ALREADY_PARTICIPATES = (
        'This player is already participating in the game.'
    )
    LEVEL_NOT_ALLOWED = (
        'Level of the player {grade} is not allowed in this game. '
        'Allowed levels: {levels}'
    )
    VALUE_MUST_BE_INTEGER = 'The value must be integer.'
    TEAMS_NUMBER_RANGE = (
        'Number of teams must be between {minimal} and {maximal}!'
    )
