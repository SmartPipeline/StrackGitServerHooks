# coding=utf8
# Copyright (c) 2019 CineUse

import traceback
from src.utils.get_arg_parser import get_arg_parser
from src.utils.parse_args import parse_args
from src.utils.get_strack_api import get_strack_api
from flask import Flask
from flask_restplus import Api, Resource


app = Flask(__name__)
api = Api(app)
hook_namespace = api.namespace('git_hook', description='post from github/gitee web hooks.')


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
@hook_namespace.route('/strack_hook')
class GiteePullRequest(Resource):
    st_info = {
        'url': 'https://cineuse.strack.vip/strack',
        'login': 'gitee',
        'passwd': 'gitee2Strack'
    }

    password = 'CvIkY1V73fi5ikU4'

    @property
    def st(self):
        return get_strack_api(self.st_info.get('url'), self.st_info.get('login'), self.st_info.get('passwd'))

    @hook_namespace.response(201, 'User successfully created.')
    @hook_namespace.doc('create a new user')
    @hook_namespace.expect(PARSER)
    def post(self):
        if not self.st:
            return u'Strack信息有误', 403
        try:
            # 解析payload
            args = parse_args(PARSER)
            pull_request_info = args.get('pull_request', {})
            if not pull_request_info:
                return u'没找到pull request信息', 403
            # 判断pr被merge的时候，结束对应的strack任务
            if args.get('action') == 'merge':
                branch_name = args.get('source_branch')
                st_issue = self.st.find_one('client', [['code', '=', branch_name]])
                if not st_issue:
                    return u'Issue %s 不存在，未做任何修改' % branch_name, 200
                # update st_task
                approved_status = self.st.find_one('status', [['code', '=', 'approved']])
                # merged_at = pull_request_info.get('merged_at')    获取合并的时间
                new_data = {
                    'status_id': approved_status.get('id'),
                    # 'end_time': merged_at  # 设置结束时间
                }
                result = self.st.update('client', st_issue.get('id'), new_data)
                return u'已更新Issue信息，从Strack得到返回内容： %s' % result, 201

            return u'未做任何修改', 200
        except Exception as e:
            return traceback.format_exc(), 400


if __name__ == '__main__':
    app.run(debug=True)
