from google.cloud import storage


def _get_client() -> storage.Client:
    return storage.Client()


def read_file(bucket: str, file_path: str) -> bytes:
    bucket_obj = _get_client().bucket(bucket)
    blob = bucket_obj.blob(file_path)
    return blob.download_as_bytes()


def write_file(bucket: str, file_path: str, data: bytes) -> None:
    bucket_obj = _get_client().bucket(bucket)
    blob = bucket_obj.blob(file_path)
    blob.upload_from_string(data)


def delete_file(bucket: str, file_path: str) -> None:
    bucket_obj = _get_client().bucket(bucket)
    blob = bucket_obj.blob(file_path)
    blob.delete()
