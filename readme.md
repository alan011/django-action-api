# Django Action API

## 简介

django-action-api是一个基于django的API框架，原生支持异步任务处理，不依赖celery这种三方组件。

API封装了request与reponse处理过程，开发者只需写对应action的handler处理方法即可。

API非RESTful设计，这是因为，设计这套框架的初衷，是为了在运维开发领域中使用。而运维开发，操作类偏多，资源类相对偏少，把所有操作抽象为资源的方式不够便捷、不够直观。故，这里把所有接口都抽象为一个action，都用POST方法通过传JSON来交互，每个action对应的一个handler处理函数。这样设计，更符合运维开发领域的思维逻辑。

最后，这是一个小巧、（核心代码）精简、灵活、开放的API框架，鼓励各位开发者在自己的项目中阅读、修改框架源码，并在此提出宝贵意见。

也可以给我发邮件：alan001lhl@163.com

## 主要特点

* 原生支持异步

集成了tornado异步非阻塞处理模块，支持高并发任务处理。采用`TCP C/S`模式处理异步任务，不依赖中间件broker，无需安装三方组件。

值得一提的是，django+celery的异步模式中常见的DB链接不释放的问题，在本框架的异步模块中，也得到完美解决（采用django原生方式释放DB连接，支持django的`CONN_MAX_AGE`全局配置参数）。

* 递归校验

对于请求的JSON数据参数，支持绝大多数场景的递归嵌套校验。

* 灵活的数据序列化

提供各种序列化Mixin工具，分层封装，对常规的增、删、改、查数据操作，提供灵活的、分层的序列化支持。可按需从不同层级接入序列化工具，开发灵活。

另外，列表数据的序列化支持分页操作。

* 提供cron定时器

集成timer定时任务模块，支持every、crontab两种方式运行定时任务

* 提供接口权限管理控制模块

* 提供action请求记录模块

* 提供API的token管理工具

* 提供一系列运维开发领域的常用工具

## 安装

将corelib目录整个放到django项目根目录即可。

需pip安装的依赖软件包：

```text
Django
mysqlclient
tornado
jsonfield
# ansible  # 如果需要用到corelib/tools/ansible_runner.py工具的话。
```

## 示例代码

一个示例django app，实现了对数据表的常规增、删、改、查操作的一组action接口。

代码结构：

```script
some_django_app/
    api.py
    handlers.py
    models.py
    urls.py
```

包含序列化设置的models.py

```python
from django.db import models
from django.utils import timezone


class HostENV(models.Model):
    id = models.AutoField('ID', primary_key=True)
    name = models.CharField('环境名称', max_length=32, default='')


class CMDBHost(models.Model):
    id = models.AutoField('ID', primary_key=True)
    hostname = models.CharField('主机名', max_length=64, default='')
    hostip = models.CharField('主机IP', max_length=32, default='')
    env = models.ForeignKey(HostENV, on_delete=models.SET_NULL, related_name='hosts', null=True)
    status = models.CharField('主机状态', max_length=32, default='')
    create_time = models.DateTimeField('创建时间', default=timezone.now)

    # 序列化设置
    list_fields = [
        'id', 'hostname', 'hostip',  # 直接取值的字段
        {'env': ['id', 'name']},  # 关系型字段的序列化，支持多级嵌套
    ]
    search_fields = ['hostname', 'hostip']  # 搜索设置。列表序列化器，将会在这两个字段中做模糊搜索，取并集。
    filter_fields = [  # 精确过滤字段，多个字段取交集。
        'status',
        'env.name',  # 关系型用'.'来串联层级关系，支持多级串联。
    ]
    detail_fields = list_fields + ['create_time']  # 时间类型序列化时，将自动转换为对应格式的字符串，默认格式'%F %T'，支持自定义。

```

常规增、删、改、查的handlers.py示例

```python
from corelib import APIHandlerBase, ChoiceType, pre_handler, StrType, IntType, ObjectType, IPType
from corelib.api_data_serializing_mixins.get_list_data_mixin import ListDataMixin
from corelib.api_data_serializing_mixins.add_data_mixin import AddDataMixin
from corelib.api_data_serializing_mixins.get_detail_data_mixin import DetailDataMixin
from corelib.api_data_serializing_mixins.modify_data_mixin import ModifyDataMixin
from corelib.api_data_serializing_mixins.delete_data_mixin import DeleteDataMixin
from .models import HostENV, CMDBHost


class HostGetHandler(APIHandlerBase, ListDataMixin, DetailDataMixin):
    post_fields = {  # post数据自动校验设置
        'search': StrType(),  # 表示接受任意字符串
        'env.name': StrType(),  # list数据的filter设置。需跟models中的filter_fields保持一致。
        'status': ChoiceType('running', 'stopped'),  # list数据的filter设置。只能传递这两个值之一，否则校验返回失败
        'page_length': IntType(min=1),  # 分页单页数据条数
        'page_index': IntType(min=1),  # 分页页面index
        'id': ObjectType(model=CMDBHost),  # 校验之后将得到一个db数据对象
    }

    @pre_handler(opt=['search', 'group.name', 'coding_type', 'page_length', 'page_index'])
    def getHostList(self):  # action处理函数
        self.getList(model=CMDBHost)

    @pre_handler(req=['id'])
    def getHostDetail(self):
        self.getDetail(model=CMDBHost)


class HostWriteHandler(APIHandlerBase, AddDataMixin, ModifyDataMixin, DeleteDataMixin):
    post_fields = {  # post数据自动校验设置
        'hostname': StrType(regex='^H', min_length=16, max_length=32),  # 必须以H开头，长度介于16到32的字符串
        'hostip': IPType(),  # IP格式的校验。
        'env': ObjectType(model=HostENV),
        'id': ObjectType(model=CMDBHost),
    }

    @pre_handler(req=['hostname', 'env'], opt=['hostip'])  # req为post数据中必须提供的字段，opt为可选。不在这两个列表中的字段，将被自动忽略。
    def addHost(self):
        self.addData(model=CMDBHost)

    @pre_handler(req=['id'])
    def deleteHost(self):
        self.deleteData()

    @pre_handler(req=['id'], opt=['hostname', 'env', 'hostip'])
    def modiyHost(self):
        self.modifyData()

# 所有的handler函数无需return，处理结果设置在handler的固有属性即可，比如：
# 若不用序列化工具，可自行做ORM数据查询，然后设置`self.data`与`self.message`即可，
# 关于这点，以及如何抛错，后面会有详细示例。
#
# pre_handler装饰器，集成了post数据自动校验、权限检查、action请求记录等功能，
# 如果数据校验失败，在pre_handler中就会直接返回`status_code=400`的错误，action函数不会执行。
# 若一个action接口不需要pre_handler中的这些功能，action方法也可不用这个装饰器。
#
# 一般将get和write做分开定义，方便做权限控制。权限控制请参考后续的示例代码。
#
# 更多字段校验格式请查阅源码: `corelib/api_base/api_field_types.py`。
# 也可修改源码，自定义数据校验格式。
# 注意：自定义字段校验格式需满足check约定。

```

将定义好的handler与action处理函数注册到api.py中

```python
from corelib import APIIngressBase
from .handlers import HostGetHandler, HostWriteHandler


class APIIngress(APIIngressBase):  # 请求会自动根据此处的actions定义来分发到handler
    actions = {
        'getHostList': HostGetHandler,  # key需保持和实际的处理函数名称一至。
        'getHostDetail': HostGetHandler,
        'addHost': HostWriteHandler,
        'deleteHost': HostWriteHandler,
        'modiyHost': HostWriteHandler,
    }

```

一个基本上固定不变的urls.py

```python
from django.urls import path
from .api import APIIngress

urlpatterns = [
    path('api/v1', APIIngress.as_view()),
]

```

最后，别忘了在django的settings.py中添加此app，以及将此处的urls.py注册到django的全局urls.py中。

注意：一般一个django app只需在全局urls.py定义中，定义一个path即可。可有效避免过于复杂的url匹配规则，引起意料之外的错误。

## 请求体数据格式与返回数据格式

采用POST方法请求，post数据采用json格式传递，并满足以下要求：

```python
{
    "action": "getHost",  # 对应的action
    # "auth_token": "xxxxxxxxxxxxxx",  # 若提供，则走token认证，否则走session认证。
    # ...其他字段
}
```

关于数据返回，若处理正确则返回一个JSON字典， status_code为200：

```python

{
    "result": "SUCCESS",  # Or "FAILED", 如果有内容上的错误。
    "data": ...  # 任意数据
    "message": "一条文字消息"
}

```

如果出现了系统级别的错误，则会返回一个字符串，status_code将为4xx或5xx（可自定义）。

## 异步任务

由于django是个同步框架，无法直接在view函数中实现异步逻辑，仍然需要借助一个独立进程来跑异步任务。

Action API异步模块提供一个独立运行的异步服务，通RPC调用来执行异步任务。

异步模块，主要用于执行一些耗时长的阻塞任务，在tornado的ioloop中，将放到线程类executor中执行。

异步模块: `corelib.asynctask`

异步服务程序：`corelib/asynctask/bin/asynctask_server`

### 一个简单示例

异步代码结构要求：

```script
some_django_app/
    api.py
    asynctasks.py  # 异步任务模块，模块名称（文件名前缀），可以通过配置项`ASYNCTASK_REGISTER_MODULE`在settings中设定
    handlers.py
    models.py
    urls.py
```

一个没啥用的异步任务，仅用做示例（asynctasks.py模块内容）:

```python
from corelib.asynctask.asynclib.decorators import asynctask
from corelib.tools.logger import Logger
import time

@asynctask  # 注册为一个异步任务，异步服务启动时，将以此为基准来自动注册RPC调用函数
def test_task(task_id):
    logger = Logger(trigger_level='INFO', msg_prefix='[asynctask] test_task: ')  # 一个简易的日志工具
    logger.log('start...')
    time.sleep(5)  # 运行一个阻塞任务
    print(task_id)
    logger.log('end!')

```

在handler中执行异步任务

```python
from .asynctask import test_task

class AsyncAPIHandler(APIHandlerBase):
    post_fields = {'task_id': IntType(min=0)}

    @pre_handler(req=['task_id'])
    def asyncAction(self):
        task_id = self.checked_params['task_id']  # 校验之后的参数，将被填充到self.checked_params字典中。
        err = test_task.delay(task_id=task_id)  # delay方法将发起RPC调用，故，只能传可序列化的参数。
        if err is not None:
            return self.error(err)  # 表示启动异步任务出错，self.error()方法自动设置处理结果为错误，status_code默认为400
        self.message = '异步任务已启动'

```

启动异步服务

```script

cd /path/to/your_django_project/

python3 corelib/asynctask/bin/asynctask_server project_setting_diretory.settings

# 启动过程中，异步服务会自动注册asynctask中定义的异步任务处理函数。
```

### 延迟调用

delay()方法支持固有参数delaytime，用于名副其实的延迟调用。

延迟sleep在异步模块中执行，delay()方法本身不阻塞。

```python

        ...
        err = test_task.delay(task_id=task_id, delaytime=10)  # 表示10秒后再执行异步任务。
        ...

```

可以用此方法，来执行一些一次性的定时任务。

```python
from django.utils import timezone
        ...
        run_at = <some_future_datetime_object>
        delaytime = int(run_at.timestamp() -  timezone.now().timestamp())
        err = test_task.delay(task_id=task_id, delaytime=delaytime)
        ...

```

如果需要固定的delay时间，还可以这样设置

```python
@asynctask(delaytime=10)  # 设置默认延迟10秒（而不是调用时才指定）。
def your_async_func():
    ...

```

### 任务状态跟踪、执行结果记录

`corelib.asynctask.api`提供一张表，与一组action接口，可将任务执行过程与结果记录到数据库中，并可通过固有API来做查询。

要启用此功能，需要将`corelib.asynctask.api`注册到django settings中的`INSTALLED_APPS`中，以及全局urls.py中。

然后，`asynctask`装饰器通过`tracking`参数来启用记录功能。

```python

@asynctask(tracking=True)
def your_async_func():
    ...

```

若是第一次添加，别忘了执行数据库的`migrate`。

## cron定时任务

<稍后补充>

## 更多示例

* 权限检查

<稍后补充>

* 操作记录

<稍后补充>
