from datetime import datetime, date, time
from django.db.models import ForeignKey, ManyToManyField, OneToOneField, Model


class BaseSerializingMixin(object):
    """
    集成了listDataMixin与DetailDataMixin的通用处理函数
    """
    # 默认日期转换格式
    date_format = '%F'
    time_format = '%T'
    datetime_format = '%F %T'
    datetime_serializer = None  # 自定义日期序列化函数，接受一个datetime对象，返回一个日期str

    def dateTimeSerializing(self, value):
        """
        用于将日期、时间对象的数据，转换成字符串
        """
        if not (isinstance(value, datetime) or isinstance(value, date) or isinstance(value, time)):
            return value

        # 自定义日期序列化处理
        if self.datetime_serializer is not None:
            return self.datetime_serializer(value)

        # 默认日期序列化处理
        if isinstance(value, datetime):
            value = value.strftime(self.datetime_format)
        elif isinstance(value, date):
            value = value.strftime(self.date_format)
        elif isinstance(value, time):
            value = value.strftime(self.time_format)
        return value

    def getObjAttr(self, obj, field):
        """
        获取字段值;
        关系型字段，按约定格式执行递归查找；
        关系型字段，不管有没有指定具体属性，都会返回其id。
        """
        if not isinstance(obj, Model):
            raise Exception("`obj` pass to this function must be an instance of a DB Model!")

        # 非关系型字段，直接取值。也作为递归的终止条件
        if isinstance(field, str):
            val = getattr(obj, field, None)
            if val is None:
                return field, None

            # 对未明确指定下级属性的关系型字段，仅返回下级obj的id
            if not isinstance(getattr(type(obj), field, None), property):
                if isinstance(obj._meta.get_field(field), OneToOneField) or isinstance(obj._meta.get_field(field), ForeignKey):
                    val = {'id': val.id}
                elif isinstance(obj._meta.get_field(field), ManyToManyField):
                    val = [{'id': obj.id} for obj in val.all()]

            # 处理时间类型的字段
            val = self.dateTimeSerializing(val)

            return field, val
        elif isinstance(field, dict):
            # ManyToManyField filters.
            m2m_excludes = field.get('__exclude__', None)
            m2m_filters = field.get('__filter__', None)

            # 获取关系字段名称，下级属性列表
            _tmp = [(k, v) for k, v in field.items() if k not in {'__exclude__', '__filter__'}]
            if len(_tmp) != 1:
                raise Exception(f"Relational field's serializing setting illegal: {field}")
            field_name, sub_fields = _tmp[0]
            if not isinstance(sub_fields, list) and not isinstance(sub_fields, tuple):
                raise Exception("Relational field's serializing setting illegal, sub fields must be a `list` or `tuple`!")

            sub_obj = getattr(obj, field_name, None)
            if sub_obj is None:
                return field_name, None

            sub_fields = list(sub_fields)
            if 'id' not in sub_fields:
                sub_fields.append('id')

            # ForeignKey或OneToOneField， 返回字典
            if isinstance(obj._meta.get_field(field_name), ForeignKey) or isinstance(obj._meta.get_field(field_name), OneToOneField):
                field_attrs = {}
                for sub_field in sub_fields:
                    k, v = self.getObjAttr(obj=sub_obj, field=sub_field)
                    field_attrs[k] = v
                return field_name, field_attrs

            # ManyToManyField返回列表（可做数据过滤），列表的元素是字典
            elif isinstance(obj._meta.get_field(field_name), ManyToManyField):
                attr_list = []
                sub_queryset = sub_obj.all()
                if m2m_filters:
                    for k, v in m2m_filters:
                        sub_queryset = sub_queryset.filter(**{k: v})
                if m2m_excludes:
                    for k, v in m2m_excludes:
                        sub_queryset = sub_queryset.exclude(**{k: v})
                for real_sub_obj in sub_queryset:
                    field_attrs = {}
                    for sub_field in sub_fields:
                        k, v = self.getObjAttr(obj=real_sub_obj, field=sub_field)
                        field_attrs[k] = v
                    attr_list.append(field_attrs)
                return field_name, attr_list

            # 关系属性值类型未知, 返回None，终止递归
            else:
                return field_name, None
        else:
            raise Exception("Serializing setting illegal, field must be `str` or `dict`.")
