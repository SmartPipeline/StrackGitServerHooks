# coding=utf8
# Copyright (c) 2018 CineUse
import copy
import json
import requests
from six.moves.urllib.parse import urljoin
from .utils import get_logger

log = get_logger("strack_api")

OPERATORS = {
                ">": "-gt",
                ">=": "-egt",
                "<": "-lt",
                "<=": "-elt",
                "=": "-eq",
                "==": "-eq",
                "!=": "-neq",
                "in": "-in",
                "not in": "-not-in",
                "like": "-lk",
                "not like": "-not-lk",
                "between": "-bw",
                "not between": "-not-bw"
            }


class Command(object):
    """
    command base class
    """
    cmd = None

    def __init__(self, server_object, module):
        """It's a Command...'"""
        self.__server = server_object
        self.__module = module
        self.__request = []

    @property
    def headers(self):
        return {'token': self.server.token, 'Content-Type': 'application/json'}

    @property
    def url(self):
        module_uri = self.module.get('code')
        if self.module.get('type') == 'entity':
            module_uri = 'entity'
        if '_' in module_uri:
            new_module_uri = ''
            for i, uri_part in enumerate(module_uri.split('_')):
                if i > 0:
                    uri_part = uri_part.capitalize()
                new_module_uri += uri_part
        else:
            new_module_uri = module_uri
        module_cmd = "%s/%s" % (new_module_uri, self.cmd)
        return self.__server.cmd_to_url(module_cmd)

    @property
    def server(self):
        return self.__server

    @property
    def module(self):
        return self.__module

    @property
    def request(self):
        return self.__request

    @property
    def parameters(self):
        # 命令所需的参数(参数名, 参数类型, 是否必填, 默认值)
        # should be [{'name': '', 'type': '', 'required': True, ''defaultValue'': '')]
        return []

    def __call__(self, *args, **kwargs):
        # 调用命令
        self.__request = (args, kwargs)
        payload, self.other_params = self._init_payload(args, kwargs)
        response = self._execute(payload)

        if response.status_code == 200 and response.json().get('status') == 229012:
            self.server.refresh_token()
            response = self._execute(payload)

        return self.__handle_response(response)

    def _init_payload(self, args, kwargs):
        # 初始化默认参数的值
        param_dict = copy.deepcopy(kwargs)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args)})
        payload, other_params = self._setup_params(param_dict)
        payload = self._format_params(payload)
        # self._validate_param(param_dict)
        return payload, other_params

    def _setup_params(self, param_dict):
        # 将参数组装成需要的格式
        payload = {}
        other_params = {}
        for parameter in self.parameters:
            name = parameter.get('name')
            is_payload = parameter.get('isPayload')
            if param_dict.get(name) is None:
                value = parameter.get('defaultValue')
            else:
                value = param_dict.get(name)
            if is_payload:
                payload.setdefault(name, value)
            else:
                other_params.setdefault(name, value)
        payload.setdefault('module', {'code': self.module.get('code', ''), 'id': self.module.get('id', 0)})
        return payload, other_params

    def _format_params(self, param_dict):
        # 格式化参数
        result = copy.deepcopy(param_dict)
        return result

    # def _validate_param(self, param_dict):
    #     # TODO: 验证参数是否正确
    #     type_map = {
    #         "list": list,
    #         "dict": dict,
    #         "str": basestring,
    #         "int": int,
    #         "float": float
    #     }
    #     for param_name, param_value in param_dict.items():
    #         if param_name not in self.parameters:
    #             raise ValueError("%s is not a validate argument." % param_name)
    #         param_type = filter(lambda x: x[0] == param_name, self.parameters)[0][1]
    #         if not isinstance(param_value, type_map.get(param_type)):
    #             raise ValueError(
    #                 "Argument '%s' must be a '%s' type object, not '%s'" % (param_name, param_type, type(param_value)))
    #     return True

    def _execute(self, payload):
        # 发送请求
        result = self.server.session.post(self.url, headers=self.headers, data=json.dumps(payload))
        return result

    def __handle_response(self, response):
        # 处理response
        if response.status_code == 200 and response.json().get('status') == 200:
            return self._success(response)
        elif response.status_code == 200 and (
                        response.json().get('status') in [216008, 216009, 216010, 202006]):
            return self._success(response)
        else:
            return self.__failed(response)

    def _success(self, response):
        # 成功的结果
        res = response.json()
        result = res.get("data")
        format_result = self._format_result(result)
        return format_result

    def __failed(self, response):
        # 失败的结果
        if response.status_code == 500:
            error_info = u"%s: %s" % (response.status_code, response.text)
        elif response.status_code not in [200, 500]:
            error_info = u"%s: %s" % (response.status_code, response.json().get("message"))
        elif response.status_code == 200:
            error_info = u"%s: %s" % (response.json().get('status'), response.json().get("message"))
        else:
            error_info = response.json()
        log.error(error_info)
        raise RuntimeError(error_info)

    def _format_result(self, result):
        # 格式化结果
        if not result:
            return {}
        new_result = copy.deepcopy(result)
        # add type
        new_result.update({"module": self.module})
        return new_result

    def _flat_item_info(self, item_info):
        result = {}
        for key, value in item_info.items():
            if key in [module.get('code') for module in self.server.modules] and isinstance(value, dict):
                for k, v in value.items():
                    result.setdefault('%s.%s' % (key, k), v)
            else:
                result.setdefault(key, value)
        return result


class QueryCommand(Command):

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'fields',
                 'type': 'list',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'order',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {}},
                {'name': 'page',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {"page_number": 0,
                                  "page_size": 0}},
                {'name': 'flat',
                 'type': 'bool',
                 'required': False,
                 'isPayload': False,
                 'defaultValue': False},
                ]

    def _format_params(self, param_dict):
        result = super(QueryCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = self._format_filter(filter_param)
        result.update({'filter': new_filter_param})
        # 格式化fields
        fields_param = result.get('fields')
        new_fields_param = self._format_fields(fields_param)
        result.update({'fields': new_fields_param})
        # 格式化order
        order_param = result.get('order')
        new_order_param = self._format_order(order_param)
        result.update({'order': new_order_param})
        return result

    def _format_filter(self, filter_param):
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            module = self.module.get('code')
            field_list = field.split('.')
            field_list_length = len(field_list)
            if field_list_length == 2 and field_list[0] in [m.get('code') for m in self.server.modules]:
                module = field_list[0]
                field = field_list[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            if isinstance(values, list):
                values = ','.join(map(lambda x: str(x), values))
            new_filter_param.setdefault(module, dict()).setdefault(field, [operator, values])
        return new_filter_param

    def _format_fields(self, fields_param):
        new_fields_param = {}
        for field_item in fields_param:
            field = field_item
            module = self.module.get('code')
            if '.' in field:
                module = field.split('.')[0]
                field = field.split('.')[-1]
                if field != '*':
                    new_fields_param.setdefault(module, list()).append(field)
                else:
                    new_fields_param.setdefault(module, list())
            else:
                new_fields_param.setdefault(module, list()).append(field)
        return new_fields_param

    def _format_order(self, order_param):
        new_order_param = {}
        for order_key, order_value in order_param.items():
            module = self.module.get('code')
            if '.' not in order_key:
                new_order_key = '%s.%s' % (module, order_key)
            else:
                new_order_key = order_key
            new_order_param.setdefault(new_order_key, order_value)
        return new_order_param


class FindCommand(QueryCommand):

    cmd = 'find'

    def _format_result(self, result):
        if not result:
            return {}
        # add type
        result.update({"module": self.module})
        flat = self.other_params.get('flat')
        if flat:
            new_result = self._flat_item_info(result)
        else:
            new_result = result
        return new_result


class SelectCommand(QueryCommand):

    cmd = 'select'

    def _format_result(self, result):
        flat = self.other_params.get('flat')

        def add_module(data):
            data.setdefault('module', self.module)
            if flat:
                new_data = self._flat_item_info(data)
            else:
                new_data = data
            return new_data
        # add type
        new_result = list(map(lambda x: add_module(x), result.get('rows')))
        return new_result


class SummaryCommand(QueryCommand):

    cmd = 'select'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'fields',
                 'type': 'list',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'order',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {}},
                {'name': 'page',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {"page_number": 0,
                                  "page_size": 0}}
                ]

    def _format_result(self, result):
        new_result = result.get('total')
        return new_result


class CreateCommand(Command):

    cmd = 'create'

    @property
    def parameters(self):
        return [{'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    def _format_params(self, param_dict):
        result = param_dict.get('data')
        result.setdefault('module', param_dict.get('module'))
        return result


class UpdateCommand(Command):

    cmd = 'update'

    @property
    def parameters(self):
        return [{'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    def _format_params(self, param_dict):
        result = param_dict.get('data')
        for key, value in result.items():
            if isinstance(value, list):
                value = ','.join(map(lambda x: str(x), value))
                result.update({key: value})
        result.setdefault('module', param_dict.get('module'))
        id_param = param_dict.get('id')
        result.update({'id': id_param})
        return result


class DeleteCommand(Command):

    cmd = 'delete'

    @property
    def parameters(self):
        return [{'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    def _format_result(self, result):
        return result


class UploadCommand(Command):

    cmd = 'upload'

    @property
    def parameters(self):
        return [{'name': 'file_path',
                 'type': 'str',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'server',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': self.server.get_best_media_server()},
                ]

    def _execute(self, payload):
        media_server = payload.get('server')
        media_server_url = media_server.get('upload_url')
        media_server_token = media_server.get('token')
        upload_file = payload.get('file_path')
        if not upload_file:
            return None
        with open(upload_file, 'rb') as f:
            file_data = {'Filedata': f}
            result = requests.post(media_server_url, data={'token': media_server_token}, files=file_data)
            return result

    def _format_result(self, result):
        return result


class FieldsCommand(Command):

    cmd = 'fields'

    @property
    def parameters(self):
        return [{'name': 'project_id',
                 'type': 'int',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 0}
                ]

    def _format_result(self, result):
        new_result = {}
        fixed_field = result.get("fixed_field") or {}
        custom_field = result.get("custom_field") or {}
        for key, value in fixed_field.items():
            new_result.setdefault(key, value)
        for field in custom_field:
            key = field.get('code')
            value = field.get('type')
            new_result.setdefault(key, value)
        return new_result


class RelationFieldsCommand(Command):

    cmd = 'fields'

    def _format_result(self, result):
        new_result = {}
        if result.get('relation'):
            new_result.update(result.get('relation'))
        return new_result


class GetTemplatePathCommand(Command):
    cmd = 'getTemplatePath'

    @property
    def parameters(self):
        return [{'name': 'module',
                 'type': 'str',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'template_code',
                 'type': 'string',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': ""
                 }]

    def _format_params(self, param_dict):
        module_name = param_dict.get('module')
        module_info = filter(lambda x: x.get('code') == module_name, self.server.modules)[0]
        link_id = param_dict.get('id')
        code = param_dict.get('template_code')
        result = {'module_id': module_info.get('id'), 'link_id': link_id, 'code': code}
        return result

    def _format_result(self, result):
        return result


class FindTemplatePathCommand(Command):
    cmd = 'findTemplatePath'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': []}]

    def _format_params(self, param_dict):
        result = super(FindTemplatePathCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result

    def _format_result(self, result):
        return result


class GetItemPathCommand(Command):
    cmd = 'getItemPath'

    @property
    def parameters(self):
        return [{'name': 'module',
                 'type': 'str',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'template_code',
                 'type': 'string',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': ""
                }]

    def _format_params(self, param_dict):
        module_name = param_dict.get('module')
        module_info = filter(lambda x: x.get('code') == module_name, self.server.modules)[0]
        link_id = param_dict.get('id')
        code = param_dict.get('template_code')
        result = {'module_id': module_info.get('id'), 'link_id': link_id, 'code': code}
        return result

    def _format_result(self, result):
        return result


class GetMediaDataCommand(Command):
    cmd = 'getMediaData'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    def _format_params(self, param_dict):
        result = super(GetMediaDataCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result

    def _format_result(self, result):
        new_result = result.get('param')
        return new_result


class GetMediaServerCommand(Command):
    cmd = 'getMediaServerItem'

    @property
    def parameters(self):
        return [{'name': 'server_id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]


class GetBestMediaServerCommand(Command):
    cmd = 'getMediaUploadServer'


class SaveMediaCommand(Command):

    @property
    def parameters(self):
        return [{'name': 'module',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'media_data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'usage_type',
                 'type': 'string',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 'thumb'},
                {'name': 'media_server',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': self.server.get_best_media_server()},
                ]

    def _format_params(self, param_dict):
        format_param = {}
        usage_type = param_dict.get('usage_type')
        module_name = param_dict.get('module')
        module_info = list(filter(lambda x: x.get('code') == module_name, self.server.modules))[0]
        link_id = param_dict.get('id')
        media_data = param_dict.get('media_data')
        media_server = param_dict.get('media_server')
        format_param.update({'module_id': module_info.get('id'), 'link_id': link_id})
        format_param.update({'media_data': media_data})
        format_param.update({'media_server': media_server})
        format_param.update({'type': usage_type})
        return format_param


class CreateMediaCommand(SaveMediaCommand):
    cmd = 'createMedia'


class UpdateMediaCommand(SaveMediaCommand):
    cmd = 'updateMedia'


class ClearMediaThumbnailCommand(Command):
    cmd = 'clearMediaThumbnail'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}]

    def _format_params(self, param_dict):
        result = super(ClearMediaThumbnailCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result


class GetMediaServerStatusCommand(Command):
    cmd = 'getMediaServerStatus'

    def _format_result(self, result):
        return result


class DeleteMediaServerCommand(Command):
    cmd = 'deleteMediaServer'


class AddMediaServerCommand(Command):
    cmd = 'addMediaServer'


class GetMediaFullPathCommand(Command):
    cmd = 'getSpecifySizeThumbPath'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'size',
                 'type': 'string',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 'origin'}]

    def _format_params(self, param_dict):
        result = super(GetMediaFullPathCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result

    def _format_result(self, result):
        # 格式化结果
        return result


class SelectMediaDataCommand(Command):
    cmd = 'selectMediaData'

    @property
    def parameters(self):
        return [{'name': 'server_id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'md5_name_list',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}]

    def _format_result(self, result):
        # 格式化结果
        new_result = result.get('param')
        return new_result


class EventCommand(Command):

    @property
    def url(self):
        module_uri = 'options'
        module_cmd = "%s/%s" % (module_uri, self.cmd)
        return self.server.cmd_to_url(module_cmd)

    def _init_payload(self, args, kwargs):
        # 初始化默认参数的值
        param_dict = copy.deepcopy(kwargs)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args)})
        param_dict, _ = self._setup_params(param_dict)
        param_dict = self._format_params(param_dict)
        # self._validate_param(param_dict)
        return param_dict, _

    def _setup_params(self, param_dict):
        # 将参数组装成需要的格式
        payload = {}
        other_params = {}
        for parameter in self.parameters:
            name = parameter.get('name')
            is_payload = parameter.get('isPayload')
            if param_dict.get(name) is None:
                value = parameter.get('defaultValue')
            else:
                value = param_dict.get(name)
            if is_payload:
                payload.setdefault(name, value)
            else:
                other_params.setdefault(name, value)
        return payload, other_params

    def _format_result(self, result):
        return result


class CreateEventCommand(EventCommand):

    cmd = 'add'

    @property
    def parameters(self):
        return [{'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _format_params(self, param_dict):
        param_dict.update({'type': 'custom'})
        return param_dict

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        add_request_url = event_server.get('add_url')
        data = payload.get('data')
        result = requests.post(add_request_url, headers=self.headers, data=data)
        return result


class QueryEventCommand(EventCommand):

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'fields',
                 'type': 'list',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'order',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {}},
                {'name': 'page',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {"page_number": 0,
                                  "page_size": 0}},
                {'name': 'flat',
                 'type': 'bool',
                 'required': False,
                 'isPayload': False,
                 'defaultValue': False},
                ]

    def _format_params(self, param_dict):
        result = super(QueryEventCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            module = 'event_log'
            if '.' in field:
                module = field.split('.')[0]
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            if isinstance(values, list):
                values = ','.join(map(lambda x: str(x), values))
            new_filter_param.setdefault(module, dict()).setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        # 格式化fields
        fields_param = result.get('fields')
        new_fields_param = {}
        for field_item in fields_param:
            field = field_item
            module = self.module.get('code')
            if '.' in field:
                module = field.split('.')[0]
                field = field.split('.')[-1]
                if field != '*':
                    new_fields_param.setdefault(module, list()).append(field)
                else:
                    new_fields_param.setdefault(module, list())
            else:
                new_fields_param.setdefault(module, list()).append(field)
        result.update({'fields': new_fields_param})
        # 格式化order
        order_param = result.get('order')
        new_order_param = {}
        for order_key, order_value in order_param.items():
            module = self.module.get('code')
            if '.' not in order_key:
                new_order_key = '%s.%s' % (module, order_key)
            else:
                new_order_key = order_key
            new_order_param.setdefault(new_order_key, order_value)
        result.update({'order': new_order_param})
        return result


class FindEventCommand(QueryEventCommand):

    cmd = 'find'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        find_request_url = event_server.get('find_url')
        result = requests.post(find_request_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        if not result:
            return {}
        # add type
        flat = self.other_params.get('flat')
        if flat:
            new_result = self._flat_item_info(result)
        else:
            new_result = result
        return new_result


class SelectEventCommand(QueryEventCommand):

    cmd = 'select'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        select_request_url = event_server.get('select_url')
        result = requests.post(select_request_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        flat = self.other_params.get('flat')

        def add_module(data):
            if flat:
                new_data = self._flat_item_info(data)
            else:
                new_data = data
            return new_data
        # add type
        new_result = list(map(lambda x: add_module(x), result.get('rows')))
        return new_result


class SummaryEventCommand(QueryEventCommand):

    cmd = 'select'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        select_request_url = event_server.get('select_url')
        result = requests.post(select_request_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        new_result = result.get('total')
        return new_result


class EventFieldsCommand(EventCommand):

    cmd = 'fields'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    @property
    def parameters(self):
        return [{'name': 'project_id',
                 'type': 'int',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 0}
                ]

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        fields_request_url = event_server.get('fields_url')
        result = requests.post(fields_request_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        return result.get('fixed_field', {})


class SendEmailCommand(EventCommand):

    cmd = 'send'

    @property
    def parameters(self):
        return [{'name': 'addressee_list',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'subject',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'template',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'content',
                 'type': 'string,dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _format_params(self, param_dict):
        addressee_list = param_dict.get('addressee_list')
        subject = param_dict.get('subject')
        content = param_dict.get('content')
        template = param_dict.get('template')
        addressee = ','.join(addressee_list)
        format_param = {'param': {'addressee': addressee, 'subject': subject},
                        'data': {'template': template, 'content': content}}
        return format_param

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        request_url = event_server.get('request_url')
        token = event_server.get('token')
        send_email_url = urljoin(request_url, 'email/%s?sign=%s' % (self.cmd, token))
        result = requests.post(send_email_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        return result


class GetEventServerCommand(Command):
    cmd = 'getEventLogServer'

    def _format_result(self, result):
        return result


class GetWebSocketServerCommand(Command):

    cmd = 'getWebSocketServer'

    def _format_result(self, result):
        return result


class GetEmailServerCommand(Command):

    cmd = 'getEmailServer'

    def _format_result(self, result):
        return result


class GetOptionsCommand(Command):

    cmd = 'getOptions'

    @property
    def parameters(self):
        return [{'name': 'options_name',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''}
                ]

    def _format_result(self, result):
        return result


class AddOptionsCommand(Command):

    cmd = 'addOptions'

    @property
    def parameters(self):
        return [{'name': 'options_name',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''},
                {'name': 'config',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []}
                ]

    def _format_result(self, result):
        return result


class CreateDefaultViewCommand(Command):

    cmd = 'createDefaultView'

    @property
    def parameters(self):
        return [{'name': 'page',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''},
                {'name': 'name',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''},
                {'name': 'code',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'project_id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'config',
                 'type': 'json',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []}
                ]

    def _format_result(self, result):
        return result


class FindDefaultViewCommand(Command):

    cmd = 'findDefaultView'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''}
                ]

    def _format_params(self, param_dict):
        result = super(FindDefaultViewCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result

    def _format_result(self, result):
        return result


class DeleteDefaultViewCommand(Command):

    cmd = 'deleteDefaultView'

    @property
    def parameters(self):
        return [{'name': 'page',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''},
                {'name': 'project_id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []}
                ]

    def _format_result(self, result):
        return result
