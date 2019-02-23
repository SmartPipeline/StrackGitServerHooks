# coding=utf8
# Copyright (c) 2018 CineUse
from strack import Strack
from utils import FilterParser


class StrackV1(Strack):
    def __init__(self, base_url, login_name, password, ldap=False, ldap_server=None):
        super(StrackV1, self).__init__(base_url, login_name, password, ldap, ldap_server)

        self.setup_modules()

    def setup_modules(self):
        for module_info in self.modules:
            module_code = module_info.get('code')
            module_object = StrackModule(self, module_info)
            setattr(self, module_code, module_object)


class StrackModule(object):
    def __init__(self, st, data):
        self.__st = st
        self.__detail = data

        self.__filter_parser = FilterParser()

    def __refracted_format_filter(self, filter_expr):
        filter_param = self.__filter_parser.parse(filter_expr)
        new_filter_param = {}
        for field, condition in filter_param.items():
            module = self.code
            field_list = field.split('.')
            field_list_length = len(field_list)
            if field_list_length == 2:
                module = field_list[0]
                field = field_list[-1]
            new_filter_param.setdefault(module, dict()).setdefault(field, condition)
        return new_filter_param

    @property
    def code(self):
        return self.__detail.get("code")

    @property
    def fields(self):
        return self.__st.fields(self.code)

    @property
    def relation_fields(self):
        return self.__st.relation_fields(self.code)

    @property
    def creation_fields(self):
        return self.__st.creation_require_fields(self.code)

    def select(self, filter_expr='', fields=None, order=None, page=None):
        """
        Same as st.find
        """
        command = self.__st.set_up_command(self.code, 'find')
        command._format_filter = lambda _: self.__refracted_format_filter(filter_expr)  # overwrite default method
        return command(None, fields, order, page)

    def find(self, filter_expr='', fields=None, order=None, page=None):
        """
        Same as st.find_one
        """
        command = self.__st.set_up_command(self.code, 'find_one')
        command._format_filter = lambda _: self.__refracted_format_filter(filter_expr)  # overwrite default method
        return command(None, fields, order, page)

    def summary(self, filter_expr=''):
        command = self.__st.set_up_command(self.code, 'find_one')
        command._format_filter = lambda _: self.__refracted_format_filter(filter_expr)  # overwrite default method
        return command(None)

    def create(self, data):
        return self.__st.create(self.code, data)

    def update(self, id_, data):
        return self.__st.update(self.code, id_, data)

    def delete(self, id_):
        return self.__st.delete(self.code, id_)

    def get_template_path(self, id_, template_code=''):
        return self.__st.get_template_path(self.code, id_, template_code)

    def get_item_path(self, id_, template_code):
        return self.__st.get_item_path(self.code, id_, template_code)

    def create_media(self, id_, media_data, usage_type='thumb', media_server=None):
        return self.__st.create_media(self.code, id_, media_data, usage_type, media_server)

    def update_media(self, id_, media_data, usage_type='thumb', media_server=None):
        return self.__st.update_media(self.code, id_, media_data, usage_type, media_server)
