from corelib import APIIngressBase
from .handlers import APICallingRecordHandler


class APIIngress(APIIngressBase):
    actions = {
        'getoperationlist': APICallingRecordHandler,
    }
