# coding=utf8
# Copyright (c) 2019 CineUse

import os
import imp
import inspect
from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)


def register_hooks():
    # 获取可用的hook，并注册对应的url
    active_hooks = [        # FIXME: 从数据库抓取这些信息
        {
            'name': 'GiteePullRequest',
            'url': '/gitee_strack_desktop_pr'
         }
    ]
    for hook_info in active_hooks:
        hook_name = hook_info.get('name', '')
        # 导入hook类作为resource
        hooks_dir = os.path.join(os.path.dirname(__file__), 'web_hooks')
        module_file, module_path, description = imp.find_module(hook_name, [hooks_dir])
        hook_module = imp.load_module(hook_name, module_file, module_path, description)
        hook_class = getattr(hook_module, hook_name)
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
