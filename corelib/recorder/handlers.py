from corelib import APIHandlerBase, pre_handler, ChoiceType, StrType, IntType
from corelib.api_data_serializing_mixins.get_list_data_mixin import ListDataMixin
from .models import APICallingRecord


class APICallingRecordHandler(APIHandlerBase, ListDataMixin):
    post_fields = {
        "search": StrType(),
        "result": ChoiceType("SUCCESS", "FAILED"),
        'page_index': IntType(min=1),
        'page_length': IntType(min=0),
    }

    @pre_handler(opt=["search", "result", "page_index", "page_length"], perm="admin")
    def getRecordList(self):
        self.getList(model=APICallingRecord)
