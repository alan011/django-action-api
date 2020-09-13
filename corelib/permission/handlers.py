from corelib import APIHandlerBase, pre_handler, ObjectType, ChoiceType, StrType, IntType
from corelib.permission.models import APIPermission
from .defaults import PERMISSION_GROUPS


class PermissionGet(APIHandlerBase):
    fields_defination = {
        "id": ObjectType(APIPermission),
        "search": StrType(),
        "perm_group": ChoiceType(*PERMISSION_GROUPS.keys(), allow_empty=True),
        "data_index": IntType(min=1),
        "data_length": IntType(min=0),
    }

    @pre_handler(opt=["search", "perm_group", "data_index", "data_length"], perm='admin')
    def getUserList(self):
        self.baseGetList(model=APIPermission)

    @pre_handler(req=['id'], perm='admin')
    def getUserDetail(self):
        self.baseGetDetail(model=APIPermission)

    @pre_handler(perm='admin')
    def getPermGroups(self):
        self.data = list(PERMISSION_GROUPS.keys())

    def getMyPerm(self):
        user = self.request.user
        self.data = {"perm_group": user.api_perm.perm_group, "username": user.username}


class PermissionSet(APIHandlerBase):
    fields_defination = {
        "id": ObjectType(APIPermission),
        "perm_group": ChoiceType(*PERMISSION_GROUPS.keys()),
    }
    @pre_handler(req=["id", "perm_group"], perm='admin', record=True)
    def setUserPerm(self):
        obj = self.checked_params['id']
        perm_group = self.checked_params['perm_group']

        self.message = "No change."
        if perm_group != obj.perm_group:
            obj.perm_group = perm_group
            obj.save()
            self.message = f"To set '{perm_group}' permission for user '{obj.user.username}' succeeded."
