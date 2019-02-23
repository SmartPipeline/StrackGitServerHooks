# coding=utf8
# Copyright (c) 2019 CineUse
from flask_restplus import Api
from flask import Blueprint

from .main.controller.user_controller import api as user_ns
from .main.web_hooks import hook_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='Strack Git Server Web Hooks',
          version='1.0',
          description=''
          )

# 将user下的api名称空间加到主api蓝图下
api.add_namespace(user_ns, path='/user')
api.add_namespace(hook_ns, path='/git_hook')
