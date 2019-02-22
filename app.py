# coding=utf8
# Copyright (c) 2019 CineUse
import glob
import os
import imp
import inspect
from flask import Flask
from flask_restplus import Api, Resource


app = Flask(__name__)
api = Api(app)
hook_namespace = api.namespace('git_hook', description='post from github/gitee web hooks.')

HOOKS_DIR = os.path.join(os.path.dirname(__file__), 'web_hooks')


def get_hook_class(hook_name):
    # 导入hook类作为resource
    try:
        module_file, module_path, description = imp.find_module(hook_name, [HOOKS_DIR])
        hook_module = imp.load_module(hook_name, module_file, module_path, description)
        hook_class = getattr(hook_module, hook_name)
        return hook_class
    except Exception as e:
        return


def register_hooks():
    # 获取可用的hook，并注册对应的url
    active_hooks = glob.glob(HOOKS_DIR+"/*.py")
    for hook_path in active_hooks:
        hook_name = os.path.basename(hook_path)[:-3]
        hook_class = get_hook_class(hook_name)
        # 获取url
        if inspect.isclass(hook_class) and issubclass(hook_class, Resource):
            # 添加Hook到API
            hook_namespace.add_resource(hook_class, hook_class.url)
            hook_namespace.expect(hook_class.parser)


# 注册可用的hook
register_hooks()

if __name__ == '__main__':
    app.run(debug=True)
