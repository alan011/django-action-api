class DeleteDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def deleteData(self, identifier='id', success_msg=None, error_msg=None):
        obj = self.checked_params[identifier]
        try:
            obj.delete()
        except Exception as e:
            _msg = f"Failed to delete data with '{identifier}={self.params[identifier]}'. {str(e)}" if error_msg is None else error_msg
            return self.error(_msg)

        self.message = f"To delete data succeeded." if success_msg is None else success_msg
