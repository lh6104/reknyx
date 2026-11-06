class DomainError(Exception):
    def __init__(self, status, code, message=None, *, details=None, retry_after=None):
        self.status = status
        self.code = code
        self.message = message or code.replace("_", " ").capitalize()
        self.details = details or []
        self.retry_after = retry_after
        super().__init__(self.message)
