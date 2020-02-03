from corelib import APIIngressBase
from .handlers import PermissionGet, PermissionSet


class APIIngress(APIIngressBase):
    actions = {
        'getUserList': PermissionGet,
        'getUserDetail': PermissionGet,
        'getPermGroups': PermissionGet,
        'getMyPerm': PermissionGet,
        'setUserPerm': PermissionSet,
    }
