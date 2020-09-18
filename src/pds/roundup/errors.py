# encoding: utf-8


'''🤠 PDS Roundup: Errors'''


class RoundupError(BaseException):
    '''All roundup exceptions come from ``RoundupError``'''


class MissingEnvVarError(BaseException):
    '''Error indicating that what may have been an optional environment variable
    at one time turned out to be absolutely required now.
    '''
    def __init__(self, name):
        '''We're missing an environment variable named ``name``'''
        super(MissingEnvVarError, self).__init__(f'Missing environment variable «{name}»')
