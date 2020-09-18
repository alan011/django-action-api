from django.views.generic import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from corelib import APIAuth
from .defaults import ACTION_AUTH_REQUIRED, ACTIONS_AUTH_BY_PASS

import json


@method_decorator(csrf_exempt, name='dispatch')
class APIIngressBase(View):
    actions = {}

    def post(self, request, *args, **kwargs):
        # To check post data in JSON.
        data = self.json_load(self.request)
        if isinstance(data, HttpResponse):
            return data
        action = data.get('action')
        auth_token = data.get('auth_token')

        # validate 'action'
        if not action:
            return HttpResponse("ERROR: 'action' field is required.", status=400)
        if action not in self.actions:
            return HttpResponse(f"ERROR: illegal action: '{action}'", status=400)

        # To get action func
        handler = self.actions[action](parameters=data, request=request)
        action_func = getattr(handler, action, lambda: HttpResponse("ERROR: method not accomplished by handler.", status=500))

        # authentication
        if action not in ACTIONS_AUTH_BY_PASS and ACTION_AUTH_REQUIRED:
            auth = APIAuth()
            if auth_token:
                if action_func._is_private:
                    return HttpResponse(f"ERROR: Private action '{action}' cannot authenticated by auth_token.", status=400)
                auth_result = auth.auth_by_token(auth_token)
            else:
                auth_result = auth.auth_by_session(request.user)
            if not auth_result:
                return HttpResponse("ERROR: API authentication failed", status=401)

        # To do the works.
        action_func()

        # make HttpResponse
        if handler.result:
            response_data = {"result": "SUCCESS", "message": str(handler.message)}
            if getattr(handler, 'data', None) is not None:
                response_data['data'] = handler.data
            if getattr(handler, 'data_total_length', None) is not None:
                response_data['data_total_length'] = handler.data_total_length
        else:
            response_data = {"result": "FAILED", "message": str(handler.error_message)}

        return HttpResponse(json.dumps(response_data), content_type='application/json', status=handler.http_status)

    def get(self, request, *args, **kwargs):
        return HttpResponse("GET method is not allowed.", status=403)

    def json_load(self, request, decode_type='utf-8'):
        """
        To load json data from http request.body.
        If Not a JSON data, return ERROR.
        If data not a dict, return ERROR.
        """

        try:
            post_data = json.loads(request.body.decode(decode_type))
        except Exception:
            return HttpResponse("ERROR: To load json data failed.", status=400)

        if isinstance(post_data, dict):
            return post_data
        else:
            return HttpResponse("ERROR: Post data is not a dict.", status=400)
