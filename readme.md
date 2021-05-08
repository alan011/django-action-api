# Django Action API

## 简介

Action API是一个基于django的API框架，原生支持异步任务处理，不依赖celery这种三方组件。

API封装了request与reponse处理过程，开发者只需写对应action的handler处理方法即可。

API非RESTful设计，这是因为，设计这套框架的初衷，是为了在运维开发领域中使用。而运维开发，操作类偏多，资源类相对偏少，把所有操作抽象为资源的方式不够便捷、不够直观。故，这里把所有接口都抽象为一个action，都用POST方法通过传JSON来交互，每个action对应的一个handler处理函数。这样设计，更符合运维开发领域的思维逻辑。

除了运维开发领域的各类系统外，此框架也适用于其他各种业务后台管理系统的开发。

在核心模块之外，提供了作为管理系统常用的扩展模块，可插拔式启用（即，注册django的INSTALLED_APP的方式来启用，具体参见后文详细说明。）

最后，这是一个小巧、（核心代码）精简、灵活、开放的API框架，鼓励各位开发者在自己的项目中阅读、修改框架源码，并在此提出宝贵意见。

也可以给我发邮件：alan001lhl@163.com

## 主要特点

* **原生支持异步**

集成了tornado异步非阻塞处理模块，支持高并发任务处理。采用`TCP C/S`模式处理异步任务，不依赖中间件broker，无需安装三方组件。

值得一提的是，django+celery的异步模式中常见的DB链接不释放的问题，在本框架的异步模块中，也得到完美解决（采用django原生方式释放DB连接，支持django的`CONN_MAX_AGE`全局配置参数）。

* **原生提供定时任务模块**

集成timer定时任务模块，提供简易的静态定时任务功能，支持crontab与every两种方式，来运行定时任务。

也提供较复杂动态定时任务功能，把定时任务配置数据都入库，并记录最后一次执行的执行结果。除了crontab与every外，还支持一次性定时任务at_time类型。

* **请求数据的递归校验**

对于请求的JSON数据参数，支持绝大多数场景的递归嵌套校验。

* **灵活的数据序列化**

Action API以Mixin Class的方式提供序列化工具，对常规的增、删、改、查数据操作，提供灵活的、分层的序列化支持。

分层封装，可按需从不同层级接入序列化工具，开发灵活。

另外，列表数据的序列化支持分页操作。

* **提供接口权限管理控制模块**

* **提供action请求记录模块，一般用于系统的操作审计**

* **提供API的token管理模块**

* **提供一系列运维开发领域的常用工具**

## 安装与配置

### 安装

将corelib目录整个放到django项目根目录即可。

corelib依赖软件包如下：

```text
Django
mysqlclient
tornado
jsonfield
# ansible  # 如果需要用到corelib/tools/ansible_runner.py工具的话。
```

关于python环境，请使用python3.6以上的版本;

Django尽量使用2.0以上的版本。

### 配置

corelib中的各个模块，支持一系列的配置选项，只需在django的全局settings.py中配置即可。

具体各模块儿支持的配置选项，请参考各个模块的`defaults.py`模块。

## 基础用法、核心模块

Action API中以下三个模块为核心与基础：

```shell

corelib/api_auth  # 负责接口的认证工作
corelib/api_base  # 基础封装，请求数据字段校验类型的封装。
corelib/api_serializing_mixin  # 以mixin-class的方式提供一系列常规增删改查序列化工具。

```

下面以一个示例django app，展示其用法。实现了对数据表的常规增、删、改、查操作的一组action接口。

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

# 若不提供list_fields与detail_fields，序列化时，默认展示所有字段。
```

常规增、删、改、查的handlers.py示例

```python
from corelib import APIHandlerBase, ChoiceType, pre_handler, StrType, IntType, ObjectType, IPType
from corelib.api_serializing_mixins import ListDataMixin, AddDataMixin, DetailDataMixin, ModifyDataMixin, DeleteDataMixin
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

以上即展示了基础模块的用法。

下面，对请求数据、返回数据，以及token管理，分别加以说明。

### 请求体数据格式与返回数据格式

采用POST方法请求，post数据采用json格式传递，并满足以下要求：

```python
{
    "action": "getHost",  # 对应的action
    # "auth_token": "xxxxxxxxxxxxxx",  # 若提供，则走token认证，否则走session认证。
    # ...其他字段
}
```

特别说明：`auth_token`字段用于接口的token认证，无需用户登录。故可归类于外部接口。
若想定义某一个handler作为私有接口，即，必须有用户登录才能访问（也即是必须走session认证），可以通过`pre_handler`的`private`参数来设置，例如：

```python

@pre_hander(private=True)
def some_action(self):
    pass

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

基础模块的可选配置参数，请分别参考以下defaults模块：

```shell

corelib/api_auth/defaults.py  # 接口认证相关配置。
corelib/api_base/defaults.py  # 绕过接口认证的相关配置。
corelib/api_serializing_mixins/defaults.py  # 目前只有list查询时，分页默认行为的相关配置。

```

### token管理说明

token分两种：

* 静态token

    直接写在配置文件`settings.py`中的token，通过参数`ACTION_STATIC_TOKENS`来指定，例如

    ``` python

    ACTION_STATIC_TOKENS = ['lalalalalalalalalalalallalalalalalalalallalal', 'test2222222222222222222']

    ```

    静态token直接配置，不会入库，也没有user归属，可随意配置。

    一般用于测试，不建议在生产环境中使用静态token。

* 动态token

    api_auth模块中集成了一个动态token管理工具，将token数据记录在数据库中，并可通过命令行，或者API，动态的管理token。

    动态token是一个字符串，由两部分组成：

    ```text
    <username>.<64位随机码>

    随机码由系统自动生成，不会包含字符‘.’
    ```

    这两个字段分别对应数据库中的两个字段，做存储。

    这样，可根据此处的`username`来关联真实用户，做权限控制。

    命令行的使用，请查看help文档：

    ```shell

    python3 corelib/api_auth/bin/token_manager --help

    ```

    api的启用，需要注册django项目settings的`INSTALLED_APPS`:

    ```python
    INSTALLED_APPS = [
        ...
        'corelib.api_auth.token_api',
    ]
    ```

    并注册url：

    ```python
    from django.urls import path, include

    urlpatterns = [
        path('token-manager/', include('corelib.api_auth.token_api.urls'))
    ]
    ```

    提供固定URI: `/token-manager/api/v1`

    提供token的增删改查actions，请参考模块: `corelib/api_auth/token/api.py`

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
    asynctasks.py  # 异步任务模块，模块名称可通过配置项`ASYNCTASK_REGISTER_MODULE`在settings中设定
    handlers.py
    models.py
    urls.py
```

一个没啥用的异步任务，仅用做示例（asynctasks.py模块内容）:

```python
from corelib.asynctask import asynctask
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

`corelib.asynctask.async_api`提供一张表，与一组action接口，可将任务执行过程与结果记录到数据库中，并可通过固有API来做查询。

要启用此功能，需要将`corelib.asynctask.async_api`注册到django settings.py中的`INSTALLED_APPS`中:

```python
INSTALLED_APPS = [
    ...
    corelib.asynctask.async_api,
    ...
]
```

以及全局urls.py中:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('asynctask/', include('corelib.asynctask.async_api.urls')],
```

然后，`asynctask`装饰器通过`tracking`参数来启用记录功能。

```python

@asynctask(tracking=True)
def your_async_func():
    ...

```

若是第一次添加，别忘了执行数据库的`migrate`。

最后，（按照之前的配置）可以通过以下内置API来管理异步任务结果：

固定URL: `/asynctask/api/v1`

支持的action，请参考api模块: `corelib/asynctask/api/api.py`

支持的配置参数，请参考defaults模块：`corelib/asynctask/lib/defaults.py`

## 定时任务

根据配置数据入不入库，将定时任务分为两类：

* 静态任务

    定时任务配置直接在编码时固定写死，配置数据不入库。
    timer服务启动后立即开始按配置执行。
    修改定时配置，必须重启timer进程。

* 动态任务

    定时任务配置数据写入数据库，可通过内置API动态修改（也可开发配套的前端页面做常规增删改查）。
    启动timer服务是，代码中标注为动态任务的任务函数，只是可配置的task模块，需要通过API进一步配置时间参数，才能开始执行。
    动态任务数据更新后，需等待timer做定时同步（即，加载数据库中的定时任务数据），默认同步周期为1分钟。
    这意味着，修改了动态任务数据，会在1分钟内自动生效（不会立即生效），无需重启timer进程。
    如果想立即生效，也可以通过重启timer进程来实现。

定时任务可以有三种执行方式：

* every

    周期执行，指定执行间隔，单位为秒，最小间隔1秒，0表示不启用。

* crontab

    类似linux的crontab字符串，拥有7个字段：

    ```shell
    * * * * * * *
    秒 分 时 日 月 周 年
    ```

* at_time

    在指定时间，执行一次的定时任务。

    仅动态任务支持这种方式，静态任务不支持。

下面分别举例说明。

### 静态任务

代码结构（类似asynctask模块）：

```script
some_django_app/
    api.py
    asynctasks.py
    timer.py  # 异步任务模块，模块名称可通过配置项`TIMER_REGISTER_MODULE`在settings中设定
    handlers.py
    models.py
    urls.py
```

编码示例：

```python
from corelib.timer.lib import cron
from corelib.tools.logger import Logger


# 每5秒执行一次
@cron(every=5)
def a_test_task():
    logger = Logger(msg_prefix='a_test_task(): ')
    logger.log("start...")
    time.sleep(1)
    logger.log("end!")


# 2021年，每天凌晨2点开始执行（其他年份自动失效）
@cron(crontab="0 0 2 * * * 2021")
def crontab_task():
    logger = Logger(msg_prefix='crontab_task(): ')
    logger.log("start...")
    time.sleep(10)
    logger.log("end!")


# 表示当时间的描述为0 20 40时开始执行。
# 注意'*/<num>'写法跟every不一样：
#   这里，表示当前时间位的数值，对<num>取余为0时才开始执行。
#   故，若在秒位写上'*/40'，表示秒数在’0 40'时执行;
#   如果写上'*/70'，则只能秒数只在0时执行。
#   其他时间位，依次类推
@cron(crontab="*/20 * * * * * *")
def crontab_task():
    logger = Logger(msg_prefix='crontab_task(): ')
    logger.log("start...")
    time.sleep(10)
    logger.log("end!")

```

值得一提的是，静态任务函数不可定义参数，不能传参（故，叫静态），也无法记录执行结果，只能在日志中查看执行成功还是失败。若要传参，以及记录执行结果，请使用动态任务。

最后，启动timer服务进程

```shell
cd /path/to/your/django_project/

python3 corelib/timer/bin/timer_server
```

### 动态任务

动态任务要求先在django的`INSTALLED_APPS`中注册timer的内置api:

```python
INSTALLED_APPS = [
    ...
    'corelib.timer.timer_api',
]

```

以及内置URL：

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('timer/', include('corelib.timer.timer_api.urls'))
]

```

别忘记做migration，来创建动态任务用的数据表。

代码组织结构、启动方式都跟静态任务一致，可跟静态任务写在同一个模块文件中。

编码示例：

```python

...

@cron(dynamic=True)
def unusable_task(foo, bar=None):
    '''
    这是一个测试用的动态任务

    参数：

    foo     字符串，必填。
    bar     字符串，可选。默认为None。
    '''
    logger = Logger(msg_prefix='unusable_task(): ')
    logger.log('start...')
    print(foo, bar)
    time.sleep(4)
    logger.log('end!')

# 注意：目前动态任务仍然不会记录任务函数的return值（考虑到对于return值，做序列化的复杂性，当前版本暂时不做此项支持）。
# 数据库中记录的所谓“执行结果”，仅仅指的是任务执行成功了，还是失败了。以及其他各项任务执行结果指标（具体请通过API查看）
```

这样，当timer_server启动时，便会把动态任务函数，注册到DB中，供用户做进一步配置。

特别注意：
    这里的动态任务函数，不是一个具体的可执行的任务，它更应当看做是一个任务模板，可以基于此函数来配置具体的动态任务。
    建议每一个动态任务，都编写文档说明，这样，用户在创建具体的动态任务时，才能知道如何给函数传参。

当前以注册了哪些动态任务（模板），可以通过API查看（我们编写了一个接口测试脚本）：

```python
import requests


def call(action, data=None):
    _data = {
        'action': action,

        # 要求在django的settings.py中设定一个静态token
        # ACTION_STATIC_TOKENS = ['lalalalalalalalalalalallalalalalalalalallalal']
        # 具体，请参考token管理说明。
        'auth_token': 'lalalalalalalalalalalallalalalalalalalallalal',
    }
    if data:
        _data.update(data)
    res = requests.post(url='http://127.0.0.1:8888/timer/api/v1', json=_data)  # 假设django的web服务起本地的8888端口

    print(f"status_code: {res.status_code}")
    print(f"data: {res.json()}")


# action: getAvailableCronList
# 用于返回，当前可用的动态任务（模板）函数，以及其文档说明
def get_availables():
    call('getAvailableCronList', {})


if __name__ == '__main__':
    get_availables()

```

然后便可使用已注册的动态任务（模板）来定义具体的动态任务：

```python

# action: addCron
# 新建一个名为test00001的动态定时任务。每5分钟执行一次。
def add_task():
    data1 = {
        'name': 'test00001',
        'description': '第一个测试任务',
        'task': 'testapp.timer.unusable_task',  # 动态任务模块（模板）
        'args': ['SRE'],  # 传给参数foo
        'kwargs': {'bar': '666'},  # 传给参数bar
        'every': 60 * 5
    }
    call('addCron', data1)

# 成功添加后，timer_server会自动加载新的任务，并开始按计划执行。无需重启timer_server


# action: getCronList
# 用户获取实际的动态任务列表
def get_tasks():
    call('getCronList', {})


# action: disableCron
# 禁用任务
def disable_task():
    data = {'id': 1}
    call('disableCron', data)


# action: enableCron
# 启用任务
def enable_task():
    data = {'id': 1}
    call('enableCron', data)


# action: modifyCron
# 限制只能运行100次，之后自动失效。
def modify_task():
    data1 = {
        'id': 1,
        'expired_count': 100,  # 0表示无限制
    }
    call('modifyCron', data1)


# action: modifyCron
# 直接指定失效时间，过期自动失效。
def modify_task():
    data1 = {
        'id': 1,
        'expired_count': 0,  # 0表示无限制
        'expired_time': '2021-05-10 00:00:00',
    }
    call('modifyCron', data1)

# expired_time与expired_count同时设定时，谁先达到即已谁为准。

# action: modifyCron
# 修改任务为一个at_time类型的任务。
# at_time类型的任务，会在指定时间点执行一次，然后立即失效。
# 如果执行时间，早于当前时间，timer进程加载到新配置后，会立即执行。
def modify_task():
    data1 = {
        'id': 1,
        'every': 0,  # 0 表示取消every设定
        'crontab': '',  # 空字符表示取消crontab设定。
        'at_time': '2021-05-07 07:03:00',  # 当at_time不为空，切every，crontab都没有设置时，表示是一个at_time任务。
    }
    call('modifyCron', data1)


# action: renewAtTimeTask
# 当一个at_time任务执行结束自动失效后，此action可用来重置一个at_time任务。
# 重置时，不会自动启用这个任务，别忘记重新启用此任务。
def renew():
    data = {
        'id': 1,
        'at_time': '2021-05-07 07:11:05'  # 可选参数。若不提供，则表示扔采用原来的时间。
    }

    call('renewAtTimeTask', data)
```

固定URI: `/timer/api/v1`

action请参考api模块: `corelib/timer/api/api.py`

timer支持的配置选项请参考defaults模块: `corelib/timer/lib/defaults.py`

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

固定URI: `/permission/api/v1`

action请参考api模块：`corelib/permission/api.py`

支持的配置选项，请参考defaults模块： `corelib/permission/defaults.py`

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

然后数据库做migrate。

如此，便可在装饰器`pre_handler`中，启用操作请求记录：

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

内置API的固定URI：`/record/api/v1`

支持的actions请参考模块：`corelib/recorder/api.py`

## 其他说明

最后，关于代码风格，附上corelib在开发过程中的，vscode中Python编码配置：

```json
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": [
        "--max-line-length=160",
        "--ignore=E402,F403,F405,W503,E126,E902",
    ],
```

这样，阅读corelib代码时，vscode显示就会很干净。
