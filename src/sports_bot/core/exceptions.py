"""Custom exceptions for the sports bot application."""

class SportsBotError(Exception):
    """Base exception class for all sports bot errors."""
    pass

class APIError(SportsBotError):
    """Raised when there are API-related errors."""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)

class DatabaseError(SportsBotError):
    """Raised when there are database-related errors."""
    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)

class ConfigurationError(SportsBotError):
    """Raised when there are configuration-related errors."""
    pass

class ValidationError(SportsBotError):
    """Raised when there are data validation errors."""
    def __init__(self, message: str, invalid_fields: dict = None):
        self.invalid_fields = invalid_fields or {}
        super().__init__(message)

class PlayerNotFoundError(SportsBotError):
    """Raised when a player cannot be found."""
    def __init__(self, player_name: str, suggestions: list = None):
        self.player_name = player_name
        self.suggestions = suggestions or []
        message = f"Player '{player_name}' not found"
        if suggestions:
            message += f". Did you mean: {', '.join(suggestions)}?"
        super().__init__(message)

class StatsNotFoundError(SportsBotError):
    """Raised when statistics cannot be found."""
    def __init__(self, player_name: str, stat_type: str = None, season: str = None):
        self.player_name = player_name
        self.stat_type = stat_type
        self.season = season
        message = f"Stats not found for {player_name}"
        if stat_type:
            message += f" ({stat_type})"
        if season:
            message += f" in season {season}"
        super().__init__(message)

class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        message = "API rate limit exceeded"
        if retry_after:
            message += f". Try again in {retry_after} seconds"
        super().__init__(message)

class AuthenticationError(APIError):
    """Raised when there are authentication issues with the API."""
    pass

class DataParsingError(SportsBotError):
    """Raised when there are errors parsing data from API or database."""
    def __init__(self, message: str, data_source: str = None, parsing_location: str = None):
        self.data_source = data_source
        self.parsing_location = parsing_location
        full_message = f"Error parsing data"
        if data_source:
            full_message += f" from {data_source}"
        if parsing_location:
            full_message += f" at {parsing_location}"
        full_message += f": {message}"
        super().__init__(full_message)

class InvalidSportError(ConfigurationError):
    """Raised when an invalid or unsupported sport is specified."""
    def __init__(self, sport: str, supported_sports: list = None):
        self.sport = sport
        self.supported_sports = supported_sports
        message = f"Invalid sport: {sport}"
        if supported_sports:
            message += f". Supported sports are: {', '.join(supported_sports)}"
        super().__init__(message)

class DatabaseConnectionError(DatabaseError):
    """Raised when there are database connection issues."""
    def __init__(self, message: str, connection_string: str = None):
        self.connection_string = connection_string
        super().__init__(message)

class CacheError(SportsBotError):
    """Raised when there are caching-related errors."""
    pass

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class ConfigError(Exception):
    """Exception for configuration-related errors."""
    pass

class DataError(Exception):
    """Exception for data-related errors."""
    pass 