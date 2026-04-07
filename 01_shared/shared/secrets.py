import google.cloud.secretmanager as secretmanager


def get_secrets(project_id: str, secret_id: str) -> str:
    secret_client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("utf-8")
