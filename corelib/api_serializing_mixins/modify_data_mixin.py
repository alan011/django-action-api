from django.db.models import ManyToManyField


class ModifyDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def modifyData(self, identifier='id', obj=None, success_msg=None, error_msg=None, update_fields=None):
        if obj is None:
            obj = self.checked_params.pop(identifier)
        changed = False
        for f in filter(lambda k: getattr(obj, k, None) != self.checked_params[k], self.checked_params):
            val = self.checked_params[f]
            if isinstance(obj._meta.get_field(f), ManyToManyField):  # Handle m2m field.
                getattr(obj, f).set(val)
            else:
                setattr(obj, f, val)
            changed = True
        if changed:
            try:
                obj.save(update_fields=update_fields)
            except Exception as e:
                _msg = f"Failed to modify data with '{identifier}={self.params[identifier]}'. {str(e)}" if error_msg is None else error_msg
                return self.error(_msg, return_value=False)

        self.message = f"To modify data with '{identifier}={self.params[identifier]}' succeeded." if success_msg is None else success_msg
        return changed

    def onlyUpdate(self, model, filters, values):
        """
        作为修改数据的一种快捷方式，相对modifyData方法，DB执行效率更好。但是不够灵活。
        返回匹配到的更新行数，Int型。
        """
        try:
            rows = model.objects.filter(**filters).update(**values)
        except Exception as e:
            return self.error(f"ERROR: Failed to execute SQL update. {str(e)}")

        self.message = f"{rows} row updated."
        return rows
