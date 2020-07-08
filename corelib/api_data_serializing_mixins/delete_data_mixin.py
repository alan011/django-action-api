class DeleteDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def deleteData(self, identifier='id'):
        obj = self.checked_params[identifier]
        try:
            obj.delete()
        except Exception as e:
            return self.error(f"Failed to delete data with '{identifier}={self.params[identifier]}'. {str(e)}")

        self.message = f"To delete data succeeded."
