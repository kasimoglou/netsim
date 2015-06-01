
# Exceptions thrown by the API. These resemble HTTP errors closely.

class Error(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(self, args)
        self.kwargs = kwargs
        if 'details' not in kwargs:
            self.kwargs['details'] = self.details
        if args and 'hint' not in kwargs:
            self.kwargs['hint'] = ','.join(args)

    def __repr__(self):
        return "%s(%s , %s)" % (self.__class__.__name__, self.args, self.kwargs)

class ClientError(Error):   # These correspond to 4xx status codes
    httpcode = 400

class BadRequest(ClientError):
    httpcode = 400
    details = 'Something was wrong with your request.' \
        ' Unfortunately there are no more details.'

class NotFound(ClientError):
    httpcode = 404
    details = 'The requested object does not exist in the '\
            'project repository.'

class Unauthorized(ClientError):
    httpcode = 401
    details = 'You are not authorized to perform this operation.'\

class Forbidden(ClientError):
    httpcode = 403
    details = 'The project repository has forbidden this operation'\

class Conflict(ClientError):
    httpcode = 409
    details = 'There is a conflict in the project repository, '\
        'maybe someone is also editing the same data.'

class ServerError(Error): # These correspond to 500 
    httpcode = 500
    details = 'There was a server error during the operation. Please '\
        'retry the operation, or consult the system administrator.'


