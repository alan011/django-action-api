import socket
import re
from datetime import datetime


# To define all supported field_types for operaters.
class FieldType(object):
    """
    This is the Top class of all field types class.
    All sub-classes must define a `check(self, field_value, ...)` method to validate parameters of api action handers.
    `check` method always returns a tuple: `checked_value, None` if checked successfully or `None, err_message`.
    """
    def __init__(self, **kwargs):
        self.field_name = kwargs.get('name', None)
        self.err_prefix = f"Illegal value of field '{self.field_name}': " if self.field_name else "Illegal params: "

    def failed(self, error, ingore_prefix=False):
        return None, error if ingore_prefix else self.err_prefix + error

    def check(self):
        """ Need to be rewrite by sub-classs. """
        return self.failed("ERROR: `check` method is not implemented.", ingore_prefix=True)


class BoolType(FieldType):
    """
    True or False. Default False.
    """

    def __init__(self, default=False, **kwargs):
        super().__init__(**kwargs)
        self.default = default

    def __str__(self):
        return '<BoolType>'

    def check(self, field_value=None):
        if field_value is None:
            return self.default
        return bool(field_value), None  # Means BoolType never check failed.


class StrType(FieldType):
    """
    This field type requires that field value must be a string, and can be matched with 'self.regex'.

    Initiallizing params:
        regex: can be provided at defining-time. Default '.*' to match any strings.
    """
    def __init__(self, regex='.*', **kwargs):
        super().__init__(**kwargs)
        self.regex = re.compile(regex)

    def __str__(self):
        return f"<StrType with regex='{self.regex}'>"

    def check(self, field_value):
        _field_value = str(field_value)
        if self.regex.match(_field_value):
            return _field_value, None
        return self.failed(f"Not match with regex '{self.regex}': '{field_value}'.")


class ScriptType(FieldType):
    """
    To check if field value contained dangerous command in each script line.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _pre, _suf = r'^(.*\s+|\&\&|\|\||)', r'(\s+.*|\\|)$'
        self.rules = {
            "alias": re.compile(f"{_pre}alias{_suf}"),
            "rm": re.compile(f"{_pre}rm{_suf}"),
            "mv": re.compile(f"{_pre}mv{_suf}"),
            "mysql": re.compile(f"{_pre}mysql{_suf}"),
            "redis": re.compile(rf"{_pre}redis-\w+{_suf}"),
            "mongo": re.compile(rf"{_pre}mongo-\w+{_suf}"),
        }

    def __str__(self):
        return '<ScriptType>'

    def check(self, field_value):
        commands = str(field_value).split('\n')
        for cmd in commands:
            for k, v in self.rules.items():
                if v.match(cmd):
                    return self.failed(f"Dangerous command found: '{cmd}'.")
        return field_value, None


class IntType(FieldType):
    """
    Checking value should be integer type. Or can be transform to integer type as a string number.

    Initiallizing params:
        min: Number min value.
        max: Number max value.
        string_num: If True , checking value can be string number.
        allow_empty: Only usefull when <string_num> is True. Allow checking value to be empty string ''.
        empty_return: Only usefull when both <string_num> and <allow_empty> are True. Return <empty_return> when checking value is empty string ''.
    """

    def __init__(self, min=-9999999999, max=9999999999, string_num=False, allow_empty=False, empty_return=0, **kwargs):
        super().__init__(**kwargs)
        self.min = min
        self.max = max
        self.string_num = string_num
        self.string_num_type = StrType(r'^\d+$')
        self.allow_empty = allow_empty
        self.empty_return = empty_return

    def __str__(self):
        return '<IntType>'

    def _check_value(self, value):
        if self.min <= value <= self.max:
            return value, None
        return self.failed(f"Number not in [{self.min}, {self.max}]: '{value}'.")

    def check(self, field_value=None):
        if self.string_num:
            if self.allow_empty and field_value == '':
                return self.empty_return, None
            _v, err = self.string_num_type.check(field_value)
            if err is not None:
                return self.failed(f"Illegal string number: '{field_value}'.")
            return self._check_value(int(_v))
        elif isinstance(field_value, int):
            return self._check_value(int(_v))
        return self.failed(f"Not a number: '{field_value}'.")


class ChoiceType(FieldType):
    """
    This field type requires that field value must be one of self.choices.

    Initiallizing params:
        choices: collection of choice value.
        allow_empty: If True, allow field value to be <empty_value>, which is not in <choices>.
        empty_value: Only usefull when <allow_empty> is True. Specify which value not in <choices> is extra allowed.
        empty_return: Only usefull when <allow_empty> is True. Specify which value to be returned when check successfully.
    """

    def __init__(self, *choices, allow_empty=False, empty_value=None, empty_return=None, **kwargs):
        super().__init__(**kwargs)
        self.choices = list(choices)
        self.allow_empty = allow_empty
        self.empty_value = empty_value
        self.empty_return = empty_return

    def __str__(self):
        return f"<ChoiceType with choices='{str(self.choices)}'>"

    def check(self, field_value):
        if self.allow_empty and field_value == self.empty_value:
            return self.empty_return, None
        if field_value in self.choices:
            return field_value, None
        return self.failed(f"Not in choices '{str(self.choices)}': '{field_value}'.")


class IPType(FieldType):
    """
    This field type requires that field value must be IP address or a IP subnet.

    Initiallizing params:
        check_subnet: If True, Treat field value as IP subnet to check.
    """

    def __init__(self, check_subnet=False, **kwargs):
        super().__init__(**kwargs)
        self.check_subnet = check_subnet

    def __str__(self):
        return '<IPType>'

    def _check_ip(self, value):
        try:
            socket.inet_aton(value)
        except Exception:
            return self.failed(f"Not an IP address: '{value}'.")
        return value, None

    def _check_subnet(self, value):
        err = self.failed(f"Not an IP subnet: '{value}'.")
        tmp_l = value.split('/')
        if len(tmp_l) != 2:
            return err
        _, _err = self._check_ip(tmp_l[0])
        if _err is not None:
            return err

        try:
            subnet_mask_len = int(tmp_l[1])
        except Exception:
            return err
        if not 0 <= subnet_mask_len <= 32:
            return err

        return value, None

    def check(self, field_value):
        _field_value = str(field_value)
        if self.check_subnet:
            return self._check_subnet(_field_value)
        return self._check_ip(_field_value)


class DatetimeType(FieldType):
    """
    This field type requires that field value must be a datetime string.

    Initiallizing params:
        format: datetime string format passed to function datetime.strptime().
    """

    def __init__(self, format='%Y-%m-%d %H:%M:%S', **kwargs):
        super().__init__(**kwargs)
        self.format = format

    def __str__(self):
        return f"<DatetimeType with format='{self.format}'>"

    def check(self, field_value):
        _field_value = str(field_value)
        try:
            date_time = datetime.strptime(_field_value, self.format)
        except ValueError:
            return self.failed(f"Not matched with datetime format '{self.format}': '{field_value}'.")
        return date_time, None


class DateType(FieldType):
    """
    This field type requires that field value must be a date string.

    Initiallizing params:
        format: date string format passed to function datetime.strptime().
    """

    def __init__(self, format='%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.format = format

    def __str__(self):
        return f"<DateType with format='{self.format}'>"

    def check(self, field_value):
        _field_value = str(field_value)
        try:
            val = datetime.strptime(_field_value, self.format).date()
        except ValueError:
            return self.failed(f"Not matched with date format '{self.format}': '{field_value}'.")
        return val, None


class ObjectType(FieldType):
    """
    This field type requires that field value could be used to query out a unique data object from the specified db model.

    Initiallizing params:
        model: Must be a well defined in django app's models.
        identified_by: a field name defined in <model>, which usually has a 'unique=True' defined.
        real_query: If True, query object data from by <identified_by>, return a db data object.
                    If False, only check data exists or not, return the origin value.
    """
    def __init__(self, model, identified_by='id', real_query=True, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.identified_by = identified_by
        self.real_query = real_query

    def __str__(self):
        return f"<ObjectType for Django Model>"

    def check(self, field_value):
        object_filter = {self.identified_by: field_value}
        count = self.model.objects.filter(**object_filter).count()
        if count == 0:
            return self.failed(f"No data object matched by filter: '{self.identified_by}={field_value}'.")
        elif count >= 2:
            return self.failed(f"Multi data objects found by filter: '{self.identified_by}={field_value}'.")
        value = self.model.objects.get(**object_filter) if self.real_query else field_value
        return value, None


class ListType(FieldType):
    """
    This field type requires field value must be a list, which has items matched self.item_type.

    Initiallizing params:
        item: 'None' means no restriction on item. Or can be instance of any FieldTypes, to make a recursive checking.
    """

    def __init__(self, item=None, **kwargs):
        super().__init__(**kwargs)
        self.item_type = item

    def __str__(self):
        return "<ListType with any items>" if self.item_type is None else f"<ListType with item_type='{str(self.item_type)}'>"

    def check(self, field_value):
        if isinstance(field_value, list):
            if self.item_type is None:
                return field_value, None

            items = []
            for item in field_value:
                _v, _err = self.item_type.check(item)
                if _err is not None:
                    return self.failed(f"Item '{item}' not matched with item_type '{str(self.item_type)}'.")
                items.append(_v)
            return items, None
        return self.failed(f"Not a list: '{field_value}'.")


class DictType(FieldType):
    """
    This field type requires field value must be a dict.

    Initiallizing params:
        key: 'None' means no restriction. Or can be instance of any FieldTypes, to make a recursive checking.
        val: 'None' means no restriction. Or can be instance of any FieldTypes, to make a recursive checking.
        format: A dict with fixed key, and value must be instance of any FieldTypes, to make a recursive checking.
                Param <key>, <val> will be ignored when <format> dict is provided.
        """

    def __init__(self, key=None, val=None, format=None, **kwargs):
        super().__init__(**kwargs)
        self.key_type = key
        self.val_type = val
        self.format = format

    def __str__(self):
        if isinstance(format, dict):
            return f"<DictType with format='{str(self.format)}'>"
        if self.key_type is not None:
            if self.val_type is not None:
                return f"<DictType with key_type='{str(self.key_type)}' and val_type='{str(self.val_type)}'>"
            return f"<DictType with key_type='{str(self.key_type)}' and any val>"
        if self.val_type is not None:
            return f"<DictType with any key and val_type='{str(self.val_type)}'>"
        return f"<DictType with no restriction>"

    def check(self, field_value):
        if isinstance(field_value, dict):
            _dict = {}

            # if self.format is set, use the given format to check data.
            if isinstance(self.format, dict):
                err = self.failed(f"Not matched with fixed dict format '{str(self.format)}': '{field_value}'.")
                for key, fieldtype in self.format.items():
                    if key not in field_value:
                        return err
                    val_check, _err = fieldtype.check(field_value[key])
                    if _err is not None:
                        return err
                    _dict[key] = val_check
                return _dict, None

            # else use key/val type definations to check data.
            for key, val in field_value.items():
                key_check, _err = self.key_type.check(key) if self.key_type is not None else key, None
                if _err is not None:
                    return self.failed(f"Dict key '{str(key)}' not matched with FieldType '{str(self.key_type)}'.")
                val_check, _err = self.val_type.check(val) if self.val_type is not None else val, None
                if _err is not None:
                    return self.failed(f"Dict val '{str(val)}' not matched with FieldType '{str(self.val_type)}'.")
                _dict[key_check] = val_check
            return _dict
        return self.failed(f"Not a dict: '{field_value}'.")
