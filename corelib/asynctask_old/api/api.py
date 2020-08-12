from corelib import APIIngressBase
from .handlers import AsyncTaskListAPI, AsyncTaskLogAPI


class APIIngress(APIIngressBase):
    actions = {
        'getList': AsyncTaskListAPI,
        'delete': AsyncTaskListAPI,
        'getLog': AsyncTaskLogAPI
    }
