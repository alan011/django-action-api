from corelib import APIHandlerBase, pre_handler, ChoiceType, StrType, ObjectType, ListType, DictType, IntType, DatetimeType
from corelib.api_serializing_mixins import ListDataMixin, DetailDataMixin, AddDataMixin, DeleteDataMixin, ModifyDataMixin
from .models import CronJob, AvailableTasks
from .choices import TASK_RESULT_CHOICES, TASK_ENABLE_CHOICES


class CronjobReadHandler(APIHandlerBase, ListDataMixin, DetailDataMixin):
    post_fields = {
        'search': StrType(),
        'enabled': ChoiceType(*TASK_ENABLE_CHOICES.keys()),
        'last_run_result': ChoiceType(*TASK_RESULT_CHOICES.keys()),
        'id': ObjectType(model=CronJob),
    }

    @pre_handler(opt=['search', 'enabled', 'last_run_result'])
    def getCronList(self):
        self.getList(model=CronJob)

    @pre_handler(req=['id'])
    def getCronDetail(self):
        self.getDetail(model=CronJob)

    def getFilterOptions(self):
        self.data = {
            'enabled_options': TASK_ENABLE_CHOICES,
            'task_result_options': TASK_RESULT_CHOICES,
        }


class CronjobWriteHandler(APIHandlerBase, AddDataMixin, DeleteDataMixin, ModifyDataMixin):
    post_fields = {
        'name': StrType(max_length=128),
        'description': StrType(),
        'task': StrType(regex=r'^(\w+\.)+\w+$'),
        'args': ListType(),
        'kwargs': DictType(key=StrType(regex=r'^\w+$')),
        'every': IntType(min=0),
        'at_time': DatetimeType(extra_allowed_values=[None, ]),
        'crontab': StrType(regex=r'^[\*\/\d]+[ \t]+[\*\/\d]+[ \t]+[\*\/\d]+[ \t]+[\*\/\d]+[ \t]+[\*\/\d]+[ \t]+[\*\/\d]+[ \t]+[\*\/\d]+$|^$'),
        'enabled': ChoiceType(*TASK_ENABLE_CHOICES.keys()),
        'expired_count': IntType(min=0),
        'expired_time': DatetimeType(extra_allowed_values=[None, ]),
        'id': ObjectType(model=CronJob, ),
    }

    add_data_opt_fileds = ['description', 'args', 'kwargs', 'every', 'crontab', 'enabled', 'expired_count', 'expired_time', 'at_time']
    modify_data_opt_fields = ['description', 'args', 'kwargs', 'every', 'crontab', 'expired_count', 'expired_time', 'at_time']

    @pre_handler(req=['name', 'task'], opt=add_data_opt_fileds, perm='admin')
    def addCron(self):
        '''
        非开放的action，不提供API。
        仅供timer主程序启动时，扫描、自动添加动态定时任务时使用。
        '''
        if not self.checked_params.get('every') and not self.checked_params.get('crontab') and not self.checked_params.get('at_time'):
            return self.error('ERROR: `every`, `crontab` or `at_time` must be provided.')
        self.addData(model=CronJob)

    @pre_handler(req=['id'], perm='admin')
    def deleteCron(self):
        self.deleteData()

    @pre_handler(req=['id'], opt=modify_data_opt_fields, perm='admin')
    def modifyCron(self):
        obj = self.checked_params['id']
        new_every = self.checked_params['every'] if 'every' in self.checked_params else obj.every
        new_crontab = self.checked_params['crontab'] if 'crontab' in self.checked_params else obj.crontab
        new_at = self.checked_params['at_time'] if 'at_time' in self.checked_params else obj.at_time
        if not new_every and not new_crontab and not new_at:
            return self.error('ERROR: `every`, `crontab` and `at_time` cannot be all empty!')
        self.modifyData()

    @pre_handler(req=['id'], perm='admin')
    def enableCron(self):
        obj = self.checked_params['id']
        obj.enabled = 1
        obj.save(update_fields=['enabled'])
        self.message = 'To enable cron task succeeded.'

    @pre_handler(req=['id'], perm='admin')
    def disableCron(self):
        obj = self.checked_params['id']
        obj.enabled = 0
        obj.save(update_fields=['enabled'])
        self.message = 'To disable cron task succeeded.'

    @pre_handler(req=['id'], opt=['at_time'], perm='admin')
    def renewAtTimeTask(self):
        obj = self.checked_params['id']
        obj.total_run_count = 0
        obj.last_run_start_at = None
        obj.last_run_spend_time = 0
        obj.last_run_result = ''
        if self.checked_params.get('at_time'):
            obj.at_time = self.checked_params['at_time']
        obj.save(update_fields=['total_run_count', 'last_run_start_at', 'last_run_spend_time', 'last_run_result', 'at_time'])


class AvailableTasksHandler(APIHandlerBase, ListDataMixin, AddDataMixin):
    post_fields = {
        'search': StrType()
    }

    @pre_handler(opt=['search'])
    def getAvailableCronList(self):
        self.getList(model=AvailableTasks)
