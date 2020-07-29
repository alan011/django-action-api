from django.db.models import ManyToManyField


class ModifyDataMixin(object):
    """
    作为核心功能的扩展，必须和核心类`APIHandlerBase`一起使用。
    """

    def modifyData(self, identifier='id', obj=None):
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
                obj.save()
            except Exception as e:
                return self.error(f"Failed to modify data with '{identifier}={self.params[identifier]}'. {str(e)}", return_value=False)

        self.message = f"To modify data with '{identifier}={self.params[identifier]}' succeeded."
        return changed
