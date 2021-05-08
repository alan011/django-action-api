from corelib import APIHandlerBase, pre_handler, StrType, IntType, ObjectType
from corelib.api_serializing_mixins import ListDataMixin, AddDataMixin, DeleteDataMixin, ModifyDataMixin
from .models import AuthToken
from corelib.tools.func_tools import genUUID


class AuthTokenHandler(APIHandlerBase, ListDataMixin, AddDataMixin, DeleteDataMixin, ModifyDataMixin):
    post_fields = {
        # for list
        "search": StrType(),
        'page_index': IntType(min=1),
        'page_length': IntType(min=0),

        # for add
        'username': StrType(regex=r'^[\w\.\-\_]+$', max_length=64),

        # for delete, set
        'id': ObjectType(AuthToken),
        'expired_time': IntType(min=0),
    }

    @pre_handler(opt=["search", "page_index", "page_length"], perm="admin")
    def getTokenList(self):
        self.getList(model=AuthToken)

    @pre_handler(opt=['username', 'expired_time'], perm="admin")
    def addToken(self):
        if not self.checked_params.get('username'):
            self.checked_params['username'] = genUUID(8)
        self.checked_params['token'] = genUUID(64)
        self.addData(AuthToken)

    @pre_handler(req=['id'], perm="admin")
    def deleteToken(self):
        self.deleteData()

    @pre_handler(req=['id', 'expired_time'], perm="admin")
    def setTokenExpiredTime(self):
        self.modifyData()
