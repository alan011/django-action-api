from .get_data_common import BaseSerializingMixin


class DetailDataMixin(BaseSerializingMixin):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用，最终会将self.data设置为一个字典。

    序列化约定：
    1、model的定义中，需包定义一个`detail_fields: list`属性。
    2、对于ForeignKey, MangToManyField, OneToOneField等关系型字段，
        请在`detail_fields`中以字典定义其取值层级关系，字段长度为1，key为field_name, value为下级属性；
        如没有以字典做明确指定，则默认仅返回下级obj的id；
        ForeignKey， OneToOneField字段，序列化后，会扩展成一个字典；
        ManyToManyField字段，序列化后，会扩展为一个列表，列表的元素下级obj的属性字典。
    3、多余多级关系，下级属性也可遵循以上约定，实现递归取值；
    4、日期时间类型默认按“%F %T”格式序列化；
        可通过设置`self.date_format`, `self.time_format`, `self.datetime_format`属性来自定义
    """

    def getDetail(self, model):
        obj = self.checked_params['id']
        self.data = {}
        detail_fields = getattr(model, 'detail_fields', None)
        if detail_fields is None:
            detail_fields = [f.name for f in model._meta.get_fields()]
        for field in model.detail_fields:
            k, v = self.getObjAttr(obj, field)
            self.data[k] = v
