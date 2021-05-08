from corelib import APIHandlerBase, pre_handler, IntType, StrType, ChoiceType, ObjectType
from .models import AsyncTask
from corelib.asynctask.config import ASYNC_TASK_LOGDIR, ASYNC_TASK_LOGFILE_PREFIX
import os


class AsyncTaskListAPI(APIHandlerBase):
    fields_defination = {
        'search': StrType(name='search'),
        'status': ChoiceType(*[item[0] for item in AsyncTask.STATUS_OPTIONS], allow_empty=True, name='status'),
        'result': ChoiceType(*[item[0] for item in AsyncTask.RESULT_OPTIONS], allow_empty=True, name='result'),
        'offset': IntType(min=1, name='offset'),
        'limit': IntType(min=0, name='limit'),
        'id': ObjectType(AsyncTask, name='id')
    }

    @pre_handler(opt=["search", "status", "result", "offset", "limit"])
    def getList(self):
        self.baseGetList(model=AsyncTask)

    @pre_handler(req=["id"])
    def delete(self):
        obj = self.checked_params['id']
        id, name = obj.id, obj.name
        obj.delete()
        self.message = f"To delete async task with id='{id}', name='{name}' succeeded."


class AsyncTaskLogAPI(APIHandlerBase):
    fields_defination = {
        'id': ObjectType(AsyncTask, real_query=False, name='id')
    }
    @pre_handler(req=["id"])
    def getLog(self):
        id = self.checked_params['id']
        log_file = os.path.join(ASYNC_TASK_LOGDIR, f'{ASYNC_TASK_LOGFILE_PREFIX}_{id}.log')
        self.data = [f'ERROR: Missing log file: {log_file}']
        if os.path.isfile(log_file):
            with open(log_file) as f:
                self.data = f.readlines()
