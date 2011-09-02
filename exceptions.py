class ElevatorError(Exception):
    pass

class BadRequest(ElevatorError):
    pass

class AuthorizationRequired(ElevatorError):
    pass

class Forbidden(ElevatorError):
    pass

class NotFound(ElevatorError):
    pass

class GatewayFailure(ElevatorError):
    pass

class GatewayConnectionError(ElevatorError):
    pass

class UnexpectedResponse(ElevatorError):
    pass
