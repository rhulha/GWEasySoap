class GWEasySoapError(Exception):
    """Raised when a GroupWise SOAP request fails or returns a bad status."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code
