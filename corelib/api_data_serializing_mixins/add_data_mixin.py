class AddDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def addData(self, model):
        obj = model(**self.checked_params)
        try:
            obj.save()
        except Exception as e:
            return self.error(f"Failed to add data. {str(e)}")

        self.message = f"To add data succeeded."
        return obj
