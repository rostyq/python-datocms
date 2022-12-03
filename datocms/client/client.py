from .upload import ClientUpload
from .graphql import ClientGraphQL
from .record import ClientRecord
from .job import ClientJob
from .upload_tag import ClientUploadTag
from .model import ClientModel
from .field import ClientField


__all__ = ["Client"]


class Client(
    ClientGraphQL,
    ClientRecord,
    ClientUpload,
    ClientJob,
    ClientUploadTag,
    ClientModel,
    ClientField
):
    pass