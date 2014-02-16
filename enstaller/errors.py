class EnstallerException(Exception):
    pass

class InvalidConfiguration(EnstallerException):
    pass

class AuthFailedError(EnstallerException):
    pass

class EnpkgError(EnstallerException):
    # FIXME: why is this a class-level attribute ?
    req = None
