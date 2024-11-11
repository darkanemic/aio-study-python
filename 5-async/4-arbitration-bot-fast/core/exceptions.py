class ExchangeError(Exception):
    pass

# API Errors
class APIError(ExchangeError):
    pass

class AuthenticationError(APIError):
    pass

class RateLimitError(APIError):
    pass

class InvalidRequestError(APIError):
    pass

# Data Processing Errors
class DataProcessingError(ExchangeError):
    pass

# Network and Web Errors
class WebError(Exception):
    pass

class NetworkError(WebError):
    pass

class WebConnectionError(NetworkError):
    pass

class WebTimeoutError(NetworkError):
    pass

class HTTPError(WebError):
    pass

# Local Storage Errors
class LocalStorageError(Exception):
    pass

class DiskFullError(LocalStorageError):
    pass

class StoragePermissionError(LocalStorageError):
    pass