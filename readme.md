# Django Action Framework

## 简介

django-action-framework是一个基于django的API框架，适用于运维开发领域（devops领域）的后端开发框架。

考虑运维开发领域的使用场景，此框架不追求高性能，而是极致追求开发的高效与便捷、易用。

非RESTful设计，运维开发领域，操作类偏多，把所有操作抽象为资源的方式不够便捷、不够直接。故，我们把所有接口调用都抽象为一个action，都用POST方法来交互，每个action对应后台的一个处理方法。个人觉得这样设计，更简单，更直接一些，更符合运维开发领域的思维逻辑。

## 特点

**递归校验**

对于请求数据，支持任意嵌套的JSON数据校验

**灵活的数据序列化**

**支持异步任务**

集成了异步任务模块，异步任务使用本地socket来实现rpc调用，无需像celery一样安装broker中间件。
异步任务默认不记录执行结果，要记录执行结果，可以将异步任务模块的api模块（corelib.asynctask.api），加入到django的INSTALLED_APPS中，启用异步任务backend，来记录执行结果，跟踪执行状态。corelib.asynctask.api模块提供一套api方便查看需要记录的异步任务。

**支持定时任务**

集成timer定时任务模块，支持every、crontab两种方式运行定时任务

**支持token管理**

**支持接口权限控制**

**支持接口操作审计**

**所有功能模块松耦合、可插拔**

除了核心模块外，其他功能模块均可以django app的形式来决定是否启用。