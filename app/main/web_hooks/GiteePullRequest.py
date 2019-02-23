# coding=utf8
# Copyright (c) 2019 CineUse

import traceback
from flask_restplus import Resource
from app.main.util.get_arg_parser import get_arg_parser
from app.main.util.parse_args import parse_args
from app.main.util.get_strack_api import get_strack_api
from app.main.web_hooks import hook_ns


arg_list = [
    {'name': 'action', 'type': str, 'default': '', 'required': False},
    {'name': 'pull_request', 'type': dict, 'default': '', 'required': False},
    {'name': 'number', 'type': int, 'default': '', 'required': False},
    {'name': 'iid', 'type': int, 'default': '', 'required': False},
    {'name': 'title', 'type': str, 'default': '', 'required': False},
    {'name': 'state', 'type': str, 'default': '', 'required': False},
    {'name': 'merge_status', 'type': str, 'default': '', 'required': False},
    {'name': 'merge_commit_sha', 'type': str, 'default': '', 'required': False},
    {'name': 'url', 'type': str, 'default': '', 'required': False},
    {'name': 'source_branch', 'type': str, 'default': '', 'required': False},
    {'name': 'source_repo', 'type': dict, 'default': '', 'required': False},
    {'name': 'target_branch', 'type': str, 'default': '', 'required': False},
    {'name': 'target_repo', 'type': dict, 'default': '', 'required': False},
    {'name': 'project', 'type': dict, 'default': '', 'required': False},
    {'name': 'repository', 'type': dict, 'default': '', 'required': False},
    {'name': 'author', 'type': dict, 'default': '', 'required': False},
    {'name': 'updated_by', 'type': dict, 'default': '', 'required': False},
    {'name': 'sender', 'type': dict, 'default': '', 'required': False},
    {'name': 'target_user', 'type': dict, 'default': '', 'required': False},
    {'name': 'hook_name', 'type': str, 'default': '', 'required': False},
    {'name': 'password', 'type': str, 'default': '', 'required': False},
]

PARSER = get_arg_parser(arg_list)


# @hook_ns.expect(PARSER)
@hook_ns.route('/strack_hook')
class GiteePullRequest(Resource):
    st_info = {
        'url': 'http://129.204.29.79:88/strack',
        'login': 'gitee',
        'passwd': 'gitee2Strack'
    }

    password = 'CvIkY1V73fi5ikU4'

    @property
    def st(self):
        return get_strack_api(self.st_info.get('url'), self.st_info.get('login'), self.st_info.get('passwd'))

    @hook_ns.response(201, 'User successfully created.')
    @hook_ns.doc('create a new user')
    @hook_ns.expect(PARSER)
    def post(self):
        try:
            # 解析payload
            args = parse_args(PARSER)
            #
            return args.get('action'), 201
        except Exception as e:
            return traceback.format_exc(), 400


if __name__ == "__main__":
    GiteePullRequest()
