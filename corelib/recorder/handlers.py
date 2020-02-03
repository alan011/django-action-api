from corelib import APIHandlerBase, pre_handler, ChoiceType, StrType, IntType
from .models import APICallingRecord


class APICallingRecordHandler(APIHandlerBase):
    fields_defination = {
        "search": StrType(),
        "result": ChoiceType("SUCCESS", "FAILED", allow_empty=True),
        'offset': IntType(min=1),
        'limit': IntType(min=0),
    }

    @pre_handler(opt=["search", "result", "offset", "limit"], perm="admin")
    def getRecordList(self):
        self.baseGetList(model=APICallingRecord)
