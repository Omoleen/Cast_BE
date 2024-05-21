from django.conf import settings
from storages.backends.azure_storage import AzureStorage

ACCOUNT_NAME = "castellum"
ACCOUNT_KEY = settings.AZURE_ACCOUNT_KEY
EXPIRATION_SECS = None
OVERWRITE_FILES = False


class AzureMediaStorage(AzureStorage):
    account_name = ACCOUNT_NAME  # Must be replaced by your <storage_account_name>
    account_key = ACCOUNT_KEY  # Must be replaced by your <storage_account_key>
    azure_container = "media"
    expiration_secs = EXPIRATION_SECS
    overwrite_files = OVERWRITE_FILES


class AzureStaticStorage(AzureStorage):
    account_name = ACCOUNT_NAME  # Must be replaced by your <storage_account_name>
    account_key = ACCOUNT_KEY  # Must be replaced by your <storage_account_key>
    azure_container = "static"
    expiration_secs = EXPIRATION_SECS
    overwrite_files = OVERWRITE_FILES
