from django.db.models import Q
from corelib.tools.func_tools import getattrRecursively
from corelib import config
from datetime import datetime, date, time


class APIHandlerBase(object):
    fields_defination = {}

    def __init__(self, parameters=None, request=None, set_parameters_directly=False):
        # handler parameters passed by `apiIngress`
        self.params = parameters if isinstance(parameters, dict) else {}
        self.request = request
        self.auth_token = self.params.pop("auth_token", None)
        self.action = self.params.pop("action", "")

        # data validation result.
        self.checked_params = None  # will be set in decorator `dataValidator`

        # To by pass data validation while calling this handler by other handlers or functions, not by api-ingress.
        self.set_parameters_directly = set_parameters_directly

        # handler results
        self.result = True
        self.message = ''
        self.error_message = ''
        self.http_status = 200
        self.data = None
        self.data_total_length = None

    def error(self, error_message, http_status=400, return_value=None):
        self.result = False
        self.error_message += error_message
        self.http_status = http_status
        return return_value

    def setResult(self, *handlers, data=None):
        """
        to set result from other handlers.
        """
        for handler in handlers:
            self.error_message += handler.error_message
            self.message += handler.message
            if not handler.result:
                self.result = False

        # return data can just be set once.
        if data:
            self.data = data

    def _makeSearchFilter(self, fields, value):
        q = Q(**{f"{fields.pop().replace('.', '__')}__icontains": value})
        if fields:
            return q | self._makeSearchFilter(fields, value)
        else:
            return q

    def getQueryset(self, model, filter=None, search_value=None, search_fields=None):
        # To query data by filter explicitly first.
        queryset = model.objects.all()
        if filter:
            query_filter = {f.replace('.', '__'): filter[f] for f in filter.keys()}
            queryset = model.objects.filter(**query_filter)

        # Then query data by search_value implicitly match with multi fields in search_fields.
        if search_value and search_fields:
            queryset = queryset.filter(self._makeSearchFilter(search_fields, search_value))

        return queryset

    def pagination(self, queryset, is_queryset=True):
        """
        Should only be used in handlers.
        """
        self.data_total_length = queryset.count() if is_queryset else len(queryset)
        offset = self.checked_params['offset']
        limit = self.checked_params['limit'] if self.checked_params.get('data_length') else config.LIST_DATA_DEFAULT_LIMIT
        return queryset[(offset - 1) * limit: offset * limit]

    def getObjAttr(self, obj, field, default='', datetime_format='%F %T', date_format='%F', time_format='%T'):
        """
        To handle recursive ForeignKey or OneToOne field attr like 'obj.attr1.attr2...'.
        To convert datetime field to datetime string with <datetime_format>.
        """
        value = getattrRecursively(obj, field, default)
        if isinstance(value, datetime):
            value = value.strftime(datetime_format)
        elif isinstance(value, date):
            value = value.strftime(date_format)
        elif isinstance(value, time):
            value = value.strftime(time_format)
        return value

    def baseGetList(self, model):
        """
        Should only be used in handlers.
        """
        # handle data searching and filtering.
        _chp = self.checked_params
        _filter = {f: _chp[f] for f in model.filter_fields if _chp.get(f) is not None}
        search = {"search_value": _chp.get('search'), "search_fields": list(model.search_fields)}
        search.update({'filter': _filter})
        queryset = self.getQueryset(model, **search)
        if not queryset.exists():
            self.data = []
        else:
            # pagination
            if "data_index" in _chp:
                queryset = self.pagination(queryset, is_queryset=True)
            self.data = [{f.replace('.', '_'): self.getObjAttr(obj, f) for f in model.list_fields} for obj in queryset]

    def baseGetDetail(self, model):
        obj = self.checked_params['id']
        self.data = {f.replace('.', '_'): self.getObjAttr(obj, f) for f in model.detail_fields}
