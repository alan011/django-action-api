from importlib import import_module
from .defaults import CUSTOM_PERMISSION_MODEL
from .models import APIPermission


def get_model():
    if not CUSTOM_PERMISSION_MODEL:
        return APIPermission
    # print(CUSTOM_PERMISSION_MODEL)
    module_path = CUSTOM_PERMISSION_MODEL[0]
    model_name = CUSTOM_PERMISSION_MODEL[1]
    try:
        module = import_module(module_path)
    except Exception:
        return None

    return getattr(module, model_name, None)
