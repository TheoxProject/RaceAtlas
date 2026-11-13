class AuthenticationFailed(ValueError):
    def __init__(self):
        super().__init__("Authentication failed.")


class InvalidPassword(ValueError):
    def __init__(self):
        super().__init__("Invalid password.")


class AuthenticationUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Authentication temporarily unavailable.")
