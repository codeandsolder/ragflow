"""Exception class definitions for connectors"""


class ConnectorMissingCredentialError(Exception):
    """Exception raised when required credentials are missing for a connector.

    Args:
        connector_name: Name of the connector missing credentials
    """

    def __init__(self, connector_name: str):
        super().__init__(f"Missing credentials for {connector_name}")


class ConnectorValidationError(Exception):
    """Exception raised when connector validation fails."""

    pass


class CredentialExpiredError(Exception):
    """Exception raised when credentials have expired and need refresh."""

    pass


class InsufficientPermissionsError(Exception):
    """Exception raised when the connector lacks required permissions."""

    pass


class UnexpectedValidationError(Exception):
    """Exception raised when an unexpected validation error occurs."""

    pass


class RateLimitTriedTooManyTimesError(Exception):
    """Exception raised when rate limit retries have been exhausted."""

    pass
