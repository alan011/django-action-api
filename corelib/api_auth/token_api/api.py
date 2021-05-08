from corelib import APIIngressBase
from .handlers import AuthTokenHandler


class APIIngress(APIIngressBase):
    """
    actions定义说明：

    getTokenList        获取token列表

    addToken            添加一个token

    deleteToken         删除一个token

    setTokenExpiredTime 设置token的失效时间。
    """

    actions = {
        'getTokenList': AuthTokenHandler,
        'addToken': AuthTokenHandler,
        'deleteToken': AuthTokenHandler,
        'setTokenExpiredTime': AuthTokenHandler,
    }
