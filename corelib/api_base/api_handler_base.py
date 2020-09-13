class APIHandlerBase(object):
    post_fields = {}

    def __init__(self, parameters=None, request=None, set_parameters_directly=False):
        # 由`apiIngress`传递的参数
        self.params = parameters if isinstance(parameters, dict) else {}
        self.request = request
        self.auth_token = self.params.pop("auth_token", None)
        self.action = self.params.pop("action", "")

        # 数据校验结果收集，在数据校验装饰器中设定
        self.checked_params = None

        # 将handler作为工具使用，而不是被`apiIngress`调用时，可以设置此参数，绕过数据校验逻辑
        self.set_parameters_directly = set_parameters_directly

        # 处理结果
        self.result = True
        self.message = ''
        self.error_message = ''
        self.http_status = 200
        self.data = None

    def error(self, error_message, http_status=400, return_value=None, log=True):
        """
        当处理失败时，设置error的便捷方法
        """
        self.result = False
        self.error_message += error_message
        self.http_status = http_status
        if log:
            print(self.error_message)
            err_log = {
                'action': self.action,
                'request_params': self.params,
                'error_message': self.error_message,
                'result': self.result,
                'status_code': self.http_status,
                'data': self.data
            }
            print(err_log)
        return return_value

    def setResult(self, *handlers, data=None):
        """
        用于此handler有直接调用其他handler时，合并多个handler的处理结果
        """
        for handler in handlers:
            self.error_message += handler.error_message
            self.message += handler.message
            if not handler.result:
                self.result = False

        # 跟message，error_message, result不同，data只能设置一次
        if data:
            self.data = data
