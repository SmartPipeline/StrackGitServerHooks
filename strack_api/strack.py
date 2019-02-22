# coding=utf8
# Copyright (c) 2018 CineUse
from .commands import *
from six.moves.urllib.parse import urlparse, urljoin, urlunparse
from .utils import get_logger


log = get_logger("strack_api")


class Strack(object):
    """
    the main object
    """

    COMMAND_FACTORY = {
        'find_one': FindCommand,
        'find': SelectCommand,
        'create': CreateCommand,
        'update': UpdateCommand,
        'summary': SummaryCommand,
        'delete': DeleteCommand,
        'fields': FieldsCommand,
        'relation_fields': RelationFieldsCommand
    }

    EVENT_COMMAND_FACTORY = {
        'create': CreateEventCommand,
        'find_one': FindEventCommand,
        'find': SelectEventCommand,
        'fields': EventFieldsCommand,
        'send_email': SendEmailCommand,
        'summary': SummaryEventCommand,
    }

    PUBLIC_COMMAND_FACTORY = {
        'upload': UploadCommand,
        'get_template_path': GetTemplatePathCommand,
        'find_template_path': FindTemplatePathCommand,
        'get_item_path': GetItemPathCommand,
        'create_media': CreateMediaCommand,
        'update_media': UpdateMediaCommand,
        'get_media_data': GetMediaDataCommand,
        'get_best_media_server': GetBestMediaServerCommand,
        'get_media_server': GetMediaServerCommand,
        'get_media_servers': GetMediaServerStatusCommand,
        'clear_media_thumbnail': ClearMediaThumbnailCommand,
        'get_media_full_path': GetMediaFullPathCommand,
        'select_media_data': SelectMediaDataCommand,
        'get_event_server': GetEventServerCommand,
        'get_web_socket_server': GetWebSocketServerCommand,
        'get_email_server': GetEmailServerCommand,
        'get_options': GetOptionsCommand,
        'add_options': AddOptionsCommand,
        'create_default_view': CreateDefaultViewCommand,
        'find_default_view': FindDefaultViewCommand,
        'delete_default_view': DeleteDefaultViewCommand,
    }

    def __init__(self, base_url, login_name, password, ldap=False, ldap_server=None):
        """
            base_url: 服务器网址
            login_name: 登陆名
            password: 密码
            ldap: 是否使用域信息验证
            ldap_server: 域服务器信息
        """
        if not base_url.endswith("/"):
            base_url += "/"
        self.session = requests.session()
        self.__base_url = base_url
        self.__login_name = login_name
        self.__ldap = "ldap" if ldap else ""
        self.__ldap_server = ldap_server if ldap_server else {'id': 0}
        self._scheme, self._server, self._api_base, _, _, _ = urlparse(urljoin(base_url, 'api/'))

        self.__entity_list = []
        self.__general_doc_dict = None
        self.__logger = None
        self.__user_id = None
        self.__token = self.get_token(password)
        self.__modules = self._list_modules()

        self.__public_commands = {}  #

    @property
    def base_url(self):
        return self.__base_url

    @property
    def login_name(self):
        return self.__login_name

    @property
    def token(self):
        return self.__token

    @property
    def user_id(self):
        return self.__user_id

    @property
    def name(self):
        return "Strack"

    @staticmethod
    def get_third_server_list(base_url):
        if not base_url.endswith("/"):
            base_url += "/"
        url = base_url + 'api/login/getThirdServerList'

        response = requests.post(url)
        if response.status_code == 200 and response.json().get("status") == 200:
            third_server_info = response.json().get("data", {})
            return third_server_info
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def cmd_to_url(self, cmd_url):
        api_path = urljoin(self._api_base, cmd_url)
        url = urlunparse((self._scheme, self._server, api_path, None, None, None))
        return url

    def set_token(self, token):
        self.__token = token

    def get_token(self, password):
        """request sign code"""
        cmd = 'login/in'
        url = self.cmd_to_url(cmd)
        auth = {
            'login_name': self.login_name,
            'password': password,
            'from': 'api',
            'method': self.__ldap,
            'server_id': self.__ldap_server.get('id', 0)

        }
        response = self.session.post(url, data=auth)
        if response.status_code == 200 and response.json().get("status") == 200:
            sign_info = response.json().get("data", {})
            self.__user_id = sign_info.get("user_id")
            return sign_info.get("token", "")
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def refresh_token(self):
        cmd = 'login/renewToken'
        url = self.cmd_to_url(cmd)
        auth = {
            'token': self.token
        }
        response = self.session.post(url, data=auth)
        if response.status_code == 200 and response.json().get("status") == 200:
            sign_info = response.json().get("data", {})
            if sign_info.get("token", "") is not "":
                self.set_token(sign_info.get("token", ""))
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def _list_modules(self):
        cmd = 'core/getModuleData'
        url = self.cmd_to_url(cmd)
        response = self.session.post(url, headers={"token": self.token})
        if response.status_code == 200 and response.json().get("status") == 200:
            data = response.json().get("data", {})
            module_info = data.get("rows", [])
            return module_info
        else:
            return

    @property
    def modules(self):
        """
        返回所有可以操作的模块
        Returns:

        """
        return self.__modules

    def set_up_command(self, module_name, command_name):
        if module_name in ['event', 'email']:
            module = {'code': 'event_log'}
            command_factory = self.EVENT_COMMAND_FACTORY
        else:
            if module_name in ['options']:
                module = {'code': 'options'}
            else:
                # check module in all modules
                for module in self.modules:
                    if module.get('code') == module_name:
                        break
                else:  # when no break triggered, go to else
                    log.error('Not module named %s.' % module_name)
                    raise RuntimeError('Not module named %s.' % module_name)

            command_factory = self.PUBLIC_COMMAND_FACTORY \
                if command_name in self.PUBLIC_COMMAND_FACTORY \
                else self.COMMAND_FACTORY

        CommandClass = command_factory.get(command_name)
        return CommandClass(self, module)

    def fields(self, module_name, project_id=0):
        """

        Args:
            module_name: [string] Name of module
            project_id: [int] id_ of project

        Returns: [dict] Dicts about field name and field data type in module

        """
        command = self.set_up_command(module_name, 'fields')
        return command(project_id)

    def relation_fields(self, module_name):
        """

        Args:
            module_name:

        Returns:

        """
        command = self.set_up_command(module_name, 'relation_fields')
        return command()

    def find_one(self, module_name, filter=None, fields=None, order=None, page=None, flat=False):
        """

        Args:
            module_name: [string] Name of module
            filter: [list] List of filter conditions
            fields: [list] List of fields to return
            page:
            order:

        Returns: [dict] Dict about found item in module

        """
        command = self.set_up_command(module_name, 'find_one')
        return command(filter, fields, order, page, flat)

    def find(self, module_name, filter=None, fields=None, order=None, page=None, flat=False):
        """

        Args:
            module_name: [string] Name of module
            filter: [list] List of filter conditions
            fields: [list] List of fields to return
            order: [dict] Dict about order field
            page: [dict] Dict about pageNum and pageSize

        Returns: [list] List of dicts about found item in module

        """
        # init command object
        command = self.set_up_command(module_name, 'find')
        # execute
        return command(filter, fields, order, page, flat)

    def summary(self, module_name, filter=None):
        command = self.set_up_command(module_name, 'summary')
        return command(filter)

    def create(self, module_name, data):
        """

        Args:
            module_name:
            data:

        Returns:

        """
        log.debug("Strack API create a object info in %s." % module_name)
        command = self.set_up_command(module_name, 'create')
        return command(data)

    def update(self, module_name, id_, data):
        log.debug("Strack API update a object info in %s." % module_name)
        command = self.set_up_command(module_name, 'update')
        return command(id_, data)

    def delete(self, module_name, id_):
        log.debug("Strack API delete a object info in %s." % module_name)
        command = self.set_up_command(module_name, 'delete')
        return command(id_)

    def upload(self, file_path, server=None):
        command = self.set_up_command('media', 'upload')
        return command(file_path, server)

    def get_template_path(self, module_name, id_, template_code=''):
        """
        获取指定项目的某种类型的模块的对象的路径模板
        Args:
            module_name:
            entity_id:
            project_id:
        Returns:

        """
        command = self.set_up_command('dir_template', 'get_template_path')
        return command(module_name, id_, template_code)

    def find_template_path(self, filter=None):
        """
        根据过滤条件获取路径模板
        Args:
            filter:
        Returns:

        """
        command = self.set_up_command('dir_template', 'find_template_path')
        return command(filter)

    def get_item_path(self, module_name, id_, template_code=''):
        """
        根据dir_template 求出某一对象的具体路径
        Args:
            module_name:
            id_:
            template_code:

        Returns:

        """
        command = self.set_up_command('dir_template', 'get_item_path')
        return command(module_name, id_, template_code)

    def create_media(self, module_name, id_, media_data, usage_type='thumb', media_server=None):
        """

        Args:
            module_name:
            id_:
            media_data:
            usage_type:
            media_server:

        Returns:

        """
        command = self.set_up_command('media', 'create_media')
        return command(module_name, id_, media_data, usage_type, media_server)

    def update_media(self, module_name, id_, media_data, usage_type='thumb', media_server=None):
        """

        Args:

            module_name:
            id_:
            media_data:
            usage_type:
            media_server:

        Returns:

        """
        command = self.set_up_command('media', 'update_media')
        return command(module_name, id_, media_data, usage_type, media_server)

    def get_media_data(self, filter=None):
        command = self.set_up_command('media', 'get_media_data')
        return command(filter)

    def get_best_media_server(self):
        """
        Description: 获取连接速度最快的媒体服务器

        Returns:

        """
        command = self.set_up_command('media', 'get_best_media_server')
        return command()

    def get_media_server(self, server_id):
        """
        Description: 获取指定id的媒体服务器

        Args:
            server_id:

        Returns:

        """
        command = self.set_up_command('media', 'get_media_server')
        return command(server_id)

    def get_media_servers(self):
        """

        Description: 获取所有的媒体服务器状态

        Returns:

        """
        command = self.set_up_command('media', 'get_media_servers')
        return command()

    def clear_media_thumbnail(self, filter):
        command = self.set_up_command('media', 'clear_media_thumbnail')
        return command(filter)

    def get_media_full_path(self, filter, size='origin'):
        command = self.set_up_command('media', 'get_media_full_path')
        return command(filter, size)

    def select_media_data(self, server_id, md5_name_list):
        command = self.set_up_command('media', 'select_media_data')
        return command(server_id, md5_name_list)

    def get_event_server(self):
        command = self.set_up_command('options', 'get_event_server')
        return command()

    def send_email(self, addressee_list, subject, template, content):
        command = self.set_up_command('email', 'send_email')
        return command(addressee_list, subject, template, content)

    def get_web_socket_server(self):
        command = self.set_up_command('options', 'get_web_socket_server')
        return command()

    def get_email_server(self):
        command = self.set_up_command('options', 'get_email_server')
        return command()

    def get_options(self, options_name):
        command = self.set_up_command('options', 'get_options')
        return command(options_name)

    def add_options(self, options_name, config):
        command = self.set_up_command('options', 'add_options')
        return command(options_name, config)

    def create_default_view(self, page, name, code, project_id, config):
        command = self.set_up_command('view', 'create_default_view')
        return command(page, name, code, project_id, config)

    def find_default_view(self, filter):
        command = self.set_up_command('view', 'find_default_view')
        return command(filter)

    def delete_default_view(self, page, project_id):
        command = self.set_up_command('view', 'delete_default_view')
        return command(page, project_id)
