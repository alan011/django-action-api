# Django Action API

## 简介

Action API是一个基于django的API框架，原生支持异步任务处理，不依赖celery这种三方组件。

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
from corelib.api_data_serializing_mixins import ListDataMixin, AddDataMixin, DetailDataMixin, ModifyDataMixin, DeleteDataMixin
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
from corelib.asynctask.asynclib import asynctask
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

但是，最好不要利用这个特性来做一些长时的延迟调用（延迟调用时间建议不要超过1分钟）。如果有长时延迟调用需求，请使用后面介绍的“定时任务”模块。

因为，这里仅仅是依赖asynctask-server进程做简单的sleep等待。若等待期间asynctask-server进程被重启，则调用最终就不会被执行。

### 任务状态跟踪、执行结果记录

`corelib.asynctask.api`提供一张表，与一组action接口，可将任务执行过程与结果记录到数据库中，并可通过固有API来做查询。

要启用此功能，需要将`corelib.asynctask.api`注册到django settings.py中的`INSTALLED_APPS`中:

```python
INSTALLED_APPS = [
    ...
    corelib.asynctask.api,
    ...
]
```

以及全局urls.py中:

```python
from django.urls import path, include

...

urlpatterns = [
    ...
    path('asynctask/', include('corelib.asynctask.api.urls')],
    ...
```

然后，`asynctask`装饰器通过`tracking`参数来启用记录功能。

```python

@asynctask(tracking=True)
def your_async_func():
    ...

```

若是第一次添加，别忘了执行数据库的`migrate`。

最后，（按照之前的配置）可以通过以下内置API来管理异步任务结果：

```yaml

uri: /asynctask/api/v1

actions:
  getList: '获取任务结果记录列表'
  delete: '删除一条任务结果记录'
```

## 定时任务

在此框架中，根据配置数据入不入库，将定时任务分为两类：

* 固定配置的定时任务

    类似linux的crontab的固定配置，不可动态修改。即，定时任务配置数据不入库。

* 动态配置的定时任务

    定时任务配置数据写入数据库，可通过timerClient动态修改，或者通过固有API编写页面来修改。

下面分别加以说明。

### 固定配置

<稍后补充>

### 动态配置

<稍后补充>

## 基于Action的权限检查

Action API框架通过`corelib.permission`模块，可以对每个定义的action做自动化的请求权限检查与校验。

考虑到权限方面的复杂性，Action API框架仅将权限按组划分，每个组代表一个权限等级，等级高低由等级序号判定，序号越大权限越高。

内置以下两个权限组：

```python
PERMISSION_GROUPS = {
    "admin": 2,
    "normal": 1,
}
```

若应用程序遵循此逻辑，需要增加其他权限组，请在django的全局设置settings.py中设置配置项`PERMISSION_GROUPS`。

若有更复杂的权限需求，请自行定制。

要启用此模块，请在django settings.py中启用此app:

```python
INSTALLED_APPS = [
    ...
    corelib.permission,
    ...
]
```

如此，便可在装饰器`pre_handler`中，启用权限检查。

默认权限组配置，实际上将权限切割为三个等级，如下：

```python
    ...
    @pre_handler(opt=['search', 'group.name', 'coding_type', 'page_length', 'page_index'])
    def getHostList(self):  # 无需权限检查，所有用户（包括没有明确配置权限组的用户）都可访问。
        self.getList(model=CMDBHost)

    @pre_handler(req=['id'], perm='normal')  # 仅允许normal与admin组的用户访问
    def getHostDetail(self):
        self.getDetail(model=CMDBHost)
    ...

    @pre_handler(req=['hostname', 'env'], opt=['hostip'], perm='admin')  # 仅允许admin组的用户访问
    def addHost(self):
        self.addData(model=CMDBHost)
    ...
```

当权限检查不通过时，Action API会返回403错误。

permission模块，也提供一组内置API，注册全局urls.py便可启用:

```python
from django.urls import path, include

...

urlpatterns = [
    ...
    path('permission/', include('corelib.permission.urls')],
    ...
```

别忘记做数据库的migration.

以此，提供用户权限设置的相关的简单action api:

```yaml

uri: /permission/api/v1

actions:
  getUserList: '获取用户列表',
  getUserDetail: '获取用户信息',  # 部分属性基于django User原生。
  getPermGroups: '获取权限组列表',
  getMyPerm: '获取当前用户的权限组',
  setUserPerm: '设置用户权限组',
```

## 基于Action的请求记录

Action API框架可通过`corelib.record`模块来对action的每一次请求做记录、入库，用作操作审计，用以监管用户的操作行为。

注意，此功能适用于请求量较小、操作会产生一定影响的API。对于请求量较大的API，请不要启用此功能，会压垮数据库。

同样需要注册APP来启用：

```python
INSTALLED_APPS = [
    ...
    corelib.recorder,
    ...
]
```

注册内置API相关URL：

```python
urlpatterns = [
    ...
    path('record/', include('corelib.recorder.urls')),
    ...
]

```

然后数据库做migration。

如此，便可在装饰器`pre_handler`中，启用操作请求记录。

默认权限组配置，实际上将权限切割为三个等级，如下：

```python
    ...
    @pre_handler(opt=['search', 'group.name', 'coding_type', 'page_length', 'page_index'])
    def getHostList(self):  # 默认不做记录
        self.getList(model=CMDBHost)
    ...

    @pre_handler(req=['hostname', 'env'], opt=['hostip'], record=True, record_label="新增host")
    def addHost(self):  # 启用请求操作记录，record_label用于对action添加可读描述。不指定则为空。
        self.addData(model=CMDBHost)
    ...
```

提供内置API：

```yaml
uri: /record/api/v1

actions:
  getRecordList: '获取操作记录列表',
```

这样，开发者只需编写简单页面即可对接此API，实现用户操作记录监控，而无需做任何后端开发。
