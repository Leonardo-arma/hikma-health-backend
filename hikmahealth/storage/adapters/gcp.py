from dataclasses import dataclass
import dataclasses
from io import BytesIO
from google.cloud import storage
from werkzeug.datastructures import FileStorage

from hikmahealth.server.client.keeper import Keeper
from hikmahealth.storage.objects import PutOutput
from .base import BaseAdapter

import os


# NOTE: might change this into a usuful function
@dataclass
class StoreConfig:
    GCP_BUCKET_NAME: str
    GCP_SERVICE_ACCOUNT: dict


def initialize_store_config_from_keeper(kp: Keeper):
    # get variables
    config = dict()

    for v in StoreConfig.__dataclass_fields__.values():
        val = kp.get(v.name)

        assert isinstance(val, v.type), "There's a type server({}) != local({})".format(
            v.type, type(val)
        )

        config[v.name] = val

    return StoreConfig(**config)


class GCPStore(BaseAdapter):
    """Adapter that makes storage possible on the Google Cloud Platform (GCP) Cloud Storage"""

    def __init__(self, bucket: storage.Bucket):
        super().__init__('gcp', '202503.01')
        self.bucket = bucket

    def download_as_bytes(self, uri: str, *args, **kwargs) -> BytesIO:
        blob = self.bucket.blob(uri)
        return BytesIO(blob.download_as_bytes())

    def put(
        self,
        data: BytesIO,
        destination: str,
        mimetype: str | None = None,
        *args,
        **kwargs,
    ):
        """saves the data to a destination"""
        assert isinstance(data, BytesIO), 'data argument needs to be a type `BytesIO`'

        # check if destination hasa a file
        blob = self.bucket.blob(destination)
        assert blob.name is not None, 'name is create from the bucket name'

        blob.upload_from_file(data, checksum='md5')

        # maybe us @dataclass later
        return PutOutput(uri=blob.name, hash=('md5', blob.md5_hash))
