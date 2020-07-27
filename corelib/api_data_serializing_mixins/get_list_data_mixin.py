from django.db.models import Q
from corelib.config import DEFAULT_PAGE_LENGTH
from .get_data_common import BaseSerializingMixin


class ListDataMixin(BaseSerializingMixin):
    """
    集成了针对列表数据的序列化处理方法，支持search与filter列表数据过滤处理。

    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用，最终会将self.data设置为一个列表。

    序列化约定：
    1、model的定义中，需包定义一个`list_fields: list`属性
    2、对于ForeignKey, MangToManyField, OneToOneField等关系型字段，
        请在`list_fields`中以字典定义其取值层级关系，字段长度为1，key为field_name, value为下级属性；
        如没有以字典做明确指定，则默认仅返回下级obj的id；
        ForeignKey， OneToOneField字段，序列化后，会扩展成一个字典；
        ManyToManyField字段，序列化后，会扩展为一个列表，列表的元素下级obj的属性字典。
    3、多余多级关系，下级属性也可遵循以上约定，实现递归取值
    4、日期时间类型默认按“%F %T”格式序列化，
        可通过设置`self.date_format`, `self.time_format`, `self.datetime_format`属性来自定义。

    分页约定：
    1、post数据中需包含'page_index'，表示当前页码
    2、post数据中可以包含'page_length'字段，表示单页的数据条数
    3、若不指定'page_length'，默认长度为`corelib.config.DEFAULT_PAGE_LENGTH`
    4、数据总条数存储在`data_total_length`属性中

    搜索约定：
    1、post数据中包含'search'字段时，调用getList，会触发多字段模糊搜索比配，具体哪些字段，请在model中定义'search_fields'
    2、post数据中包含model定义的db字段，会触发，精确的filter过滤，具体哪些字段，请在model中定义'filter_fields'
    3、关系型字段，请以'.'分隔表示层级关系
    4、当search与filter的post传值为None，或者search为空字符串时，会当做未传值处理，
        未传值则不依此来搜索/过滤，返回所有其他匹配条件的数据。
    5、特别注意：post_fields定义时，要允许为None
    """
    # 数据总长度，分页功能使用
    data_total_length = None

    def _makeSearchFilter(self, fields, value):
        """
        search搜索多个字段、模糊匹配、不区分大小写
        """
        q = Q(**{f"{fields.pop().replace('.', '__')}__icontains": value})
        if fields:
            return q | self._makeSearchFilter(fields, value)
        else:
            return q

    def pagination(self, queryset, is_queryset=True):
        """
        对queryset或者list数据执行分页计算，填充`self.data_total_length`属性
        """
        self.data_total_length = queryset.count() if is_queryset else len(queryset)
        page_index = self.checked_params['page_index']
        page_length = self.checked_params['page_length'] if self.checked_params.get('page_length') else DEFAULT_PAGE_LENGTH
        return queryset[(page_index - 1) * page_length: page_index * page_length]

    def getQueryset(self, model, filters=None, search_value=None, search_fields=None, order_by=None, excludes=None, additional_filters=None):
        """
        执行过滤，搜索，返回一个真实queryset
        """
        queryset = model.objects.all()

        # 先按filter精确过滤
        if filters:
            query_filter = {f.replace('.', '__'): filters[f] for f in filters.keys()}
            queryset = model.objects.filter(**query_filter)

        # 然后执行按search模糊搜索
        if search_value and search_fields:
            queryset = queryset.filter(self._makeSearchFilter(search_fields, search_value))

        # 执行额外的条件过滤
        if additional_filters is not None:
            for k, v in additional_filters:
                queryset = queryset.filter(**{k: v})

        # 排除过滤
        if excludes is not None:
            for k, v in excludes:
                queryset = queryset.exclude(**{k: v})

        # 排序
        if order_by is not None:
            queryset = queryset.order_by(order_by)

        return queryset.distinct()

    def _id_unique(self, list_data):
        """
        基于ManyToManyField的下级属性做过滤，会造成数据重复，在这里保证行数据不重复
        """
        tmp_set = set()
        data = []
        for raw in list_data:
            if raw['id'] not in tmp_set():
                data.append(raw)
                tmp_set.add(raw['id'])
        return data

    def _makeListData(self, queryset, model):
        """
        将queryset基于model.list_fields设置，转换成可序列化的数据列表;
        不管model.list_fields有没有指定id，都会返回id属性；
        另外，基于ManyToManyField的下级属性做过滤，会造成数据重复，在这里会保证每条数据id不重复。
        """
        list_fields = getattr(model, 'list_fields', None)
        if list_fields is None:
            list_fields = [f.name for f in model._meta.get_fields()]
        if 'id' not in list_fields:
            list_fields.append('id')

        list_data = []
        # tmp_set = set()
        for obj in queryset:
            raw = {}
            for field in list_fields:
                k, v = self.getObjAttr(obj, field)
                raw[k] = v
            list_data.append(raw)
        #     if raw['id'] not in tmp_set:
        #         tmp_set.add(raw['id'])
        #         list_data.append(raw)
        return list_data

    def getList(self, model, order_by=None, excludes=None, additional_filters=None):
        if self.checked_params is None:
            self.checked_params = {}
        search = {
            'search_value': self.checked_params.get('search'),
            'search_fields': list(getattr(model, 'search_fields', [])),
            'filters': {f: self.checked_params[f] for f in getattr(model, 'filter_fields', []) if self.checked_params.get(f) is not None},
            'order_by': order_by,
            'excludes': excludes,
            'additional_filters': additional_filters
        }
        queryset = self.getQueryset(model, **search)
        if not queryset.exists():
            self.data = []
        else:
            if "page_index" in self.checked_params:
                queryset = self.pagination(queryset)
            self.data = self._makeListData(queryset, model)
