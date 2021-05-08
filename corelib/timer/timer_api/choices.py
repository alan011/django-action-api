from collections import OrderedDict

TASK_ENABLE_CHOICES = OrderedDict()
TASK_ENABLE_CHOICES[0] = '已停用'
TASK_ENABLE_CHOICES[1] = '已启用'

TASK_RESULT_CHOICES = OrderedDict()
TASK_RESULT_CHOICES[''] = '未知'
TASK_RESULT_CHOICES['success'] = '成功'
TASK_RESULT_CHOICES['failed'] = '失败'
