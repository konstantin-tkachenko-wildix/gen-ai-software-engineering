"""Custom application exceptions mapped to HTTP responses in main.py."""


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
        super().__init__(f"Ticket '{ticket_id}' was not found")


class UnsupportedImportFormatError(Exception):
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(
            f"Unsupported file format for '{filename}'. Expected .csv, .json, or .xml"
        )


class FileParsingError(Exception):
    """Raised when a whole import file cannot be parsed at all (e.g. corrupt content)."""

    def __init__(self, message: str):
        super().__init__(message)
