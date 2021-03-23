from .client_base import K8SClientBase


class ServiceClient(K8SClientBase):
    """
    Service的增删改查
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
