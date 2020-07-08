class AddDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def addData(self, model, row_data=None):
        if not row_data:
            row_data = self.checked_params
        obj = model(**row_data)
        try:
            obj.save()
        except Exception as e:
            return self.error(f"Failed to add data. {str(e)}")

        self.message = f"To add data succeeded."
        return obj
