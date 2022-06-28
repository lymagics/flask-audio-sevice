import os
from threading import Thread
from uuid import uuid4

from firebase_admin import storage
from flask import current_app


def generate_access_token():
    """Generate access token to upload to firebase."""
    return uuid4()


def async_upload(file_name, content_type, blob):
    """Upload file to storage asyncronyously.
    
    :param file_name: name of local file to upload.
    :param content_type: type of file.
    :param blob: firebase blob object.
    """
    blob.upload_from_filename(filename=file_name, content_type=content_type)
    os.remove(file_name)


def upload_to_storage(file_name, content_type):
    """Upload file to storage.
    
    :param file_name: name of local file to upload.
    :param content_type: type of file.
    """
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    
    new_token = generate_access_token()
    metadata  = {"firebaseStorageDownloadTokens": new_token}
    
    blob.metadata = metadata
    
    thr = Thread(target=async_upload, args=[file_name, content_type, blob])
    thr.start()
    
    return thr
 
 
def delete_from_storage(file_name):
    """Delete file from storage.
    
    :param file_name: name of file to delete.
    """
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    blob.delete()
    
    
def get_public_url(file_name):
    """Get file url from storage.
    
    :param file_name: name of file to get url.
    """
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    
    blob.make_public()
    return blob.public_url
    
    