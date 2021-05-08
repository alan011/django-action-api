from corelib import APIIngressBase
from .handlers import CronjobReadHandler, CronjobWriteHandler, AvailableTasksHandler


class APIIngress(APIIngressBase):
    actions = {
        'getCronList': CronjobReadHandler,
        'getFilterOptions': CronjobReadHandler,
        'getCronDetail': CronjobReadHandler,
        'addCron': CronjobWriteHandler,
        'deleteCron': CronjobWriteHandler,
        'modifyCron': CronjobWriteHandler,
        'enableCron': CronjobWriteHandler,
        'disableCron': CronjobWriteHandler,
        'renewAtTimeTask': CronjobWriteHandler,
        'getAvailableCronList': AvailableTasksHandler,
    }
