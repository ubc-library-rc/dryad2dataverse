'''
Custom exceptions for error handling.
'''

class Dryad2DataverseError(Exception):
    '''
    Base exception class for Dryad2Dataverse errors.
    '''

class NoTargetError(Dryad2DataverseError):
    '''
    No dataverse target supplied error.
    '''

class DownloadSizeError(Dryad2DataverseError):
    '''
    Raised when download sizes don't match reported
    Dryad file size.
    '''

class HashError(Dryad2DataverseError):
    '''
    Raised on hex digest mismatch.
    '''

class DatabaseError(Dryad2DataverseError):
    '''
    Tracking database error.
    '''

class DataverseUploadError(Dryad2DataverseError):
    '''
    Returned on not OK respose (ie, not requests.status_code == 200).
    '''

class DataverseDownloadError(Dryad2DataverseError):
    '''
    Returned on not OK respose (ie, not requests.status_code == 200).
    '''

class DataverseBadApiKeyError(Dryad2DataverseError):
    '''
    Returned on not OK respose (ie, request.request.json()['message'] == 'Bad api key ').
    '''
