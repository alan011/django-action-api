from corelib import APIHandlerBase, pre_handler, ObjectType, ChoiceType, StrType, IntType
from corelib.api_serializing_mixins.get_list_data_mixin import ListDataMixin
from corelib.api_serializing_mixins.get_detail_data_mixin import DetailDataMixin
from corelib.api_serializing_mixins.modify_data_mixin import ModifyDataMixin
from .defaults import PERMISSION_GROUPS
from .tools import get_model


class PermissionGet(APIHandlerBase, ListDataMixin, DetailDataMixin):
    post_fields = {
        "id": ObjectType(get_model()),
        "search": StrType(),
        "perm_group": ChoiceType(*PERMISSION_GROUPS.keys(), allow_empty=True),
        "page_index": IntType(min=1),
        "page_length": IntType(min=0),
    }

    @pre_handler(opt=["search", "perm_group", "page_index", "page_length"], perm='admin')
    def getUserList(self):
        self.getList(model=get_model())

    @pre_handler(req=['id'], perm='admin')
    def getUserDetail(self):
        self.getDetail(model=get_model())

    @pre_handler(perm='admin')
    def getPermGroups(self):
        self.data = list(PERMISSION_GROUPS.keys())

    @pre_handler(perm='normal')
    def getMyPerm(self):
        self.data = {"perm_group": self.user_perm.perm_group, "username": self.user_perm.user.username}


class PermissionSet(APIHandlerBase, ModifyDataMixin):
    post_fields = {
        "id": ObjectType(get_model()),
        "perm_group": ChoiceType(*PERMISSION_GROUPS.keys()),
    }
    @pre_handler(req=["id", "perm_group"], perm='admin', record=True)
    def setUserPerm(self):
        self.modifyData()
