from django.db.models import ManyToManyField


class AddDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def addData(self, model, row_data=None, success_msg=None, error_msg=None):
        if not row_data:
            row_data = self.checked_params

        # To peel off ManytoManyField data.
        m2m_fields = {}
        for field in filter(lambda f: isinstance(model._meta.get_field(f), ManyToManyField), row_data):
            m2m_fields[field] = row_data[field]
        for f in m2m_fields:
            row_data.pop(f)

        # To write normal fields first
        obj = model(**row_data)
        try:
            obj.save()
        except Exception as e:
            _msg = f"Failed to add data. {str(e)}" if error_msg is None else error_msg
            return self.error(_msg)

        # Then, to set m2m fields.
        for f in m2m_fields:
            getattr(obj, f).set(m2m_fields[f])

        self.message = f"To add data succeeded." if success_msg is None else success_msg
        return obj
