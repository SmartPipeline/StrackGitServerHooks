# coding=utf8
# Copyright (c) 2019 CineUse

import os
import imp
import inspect
from flask import Flask
from flask_restful import Api, Resource

from utils.get_strack_api import get_strack_api

app = Flask(__name__)
api = Api(app)


def get_hook_class(hook_info):
    hook_name = hook_info.get('name', '')
    # 导入hook类作为resource
    hooks_dir = os.path.join(os.path.dirname(__file__), 'web_hooks')
    module_file, module_path, description = imp.find_module(hook_name, [hooks_dir])
    hook_module = imp.load_module(hook_name, module_file, module_path, description)
    hook_class = getattr(hook_module, hook_name)
    # init strack api_object
    hook_class.password = hook_info.get('hook_password')
    try:
        hook_class.st = get_strack_api(hook_info.get('strack_url'), hook_info.get('strack_login'), hook_info.get('strack_passwd'))
    except Exception:
        pass
    return hook_class


def register_hooks():
    # 获取可用的hook，并注册对应的url
    active_hooks = [        # FIXME: 从数据库抓取这些信息
        {
            'name': 'GiteePullRequest',
            'url': '/gitee_strack_desktop_pr',
            'hook_password': 'CvIkY1V73fi5ikU4',
            'strack_url': 'http://129.204.29.79:88/strack',
            'strack_login': 'gitee',
            'strack_passwd': 'gitee2Strack'
         }
    ]
    for hook_info in active_hooks:
        hook_class = get_hook_class(hook_info)
        # 获取url
        hook_url = hook_info.get('url')
        if hook_url and inspect.isclass(hook_class) and issubclass(hook_class, Resource):
            # 添加Hook到API
            api.add_resource(hook_class, hook_url)


# 注册可用的hook
register_hooks()


@app.route('/')
def index():
    # TODO: 构建一个后台管理界面，允许用户维护自己的WebHook
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)
