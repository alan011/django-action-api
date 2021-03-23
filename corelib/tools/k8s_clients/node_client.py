from .client_base import K8SClientBase


class NodeClient(K8SClientBase):
    """
    集群节点的增删改查
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass
