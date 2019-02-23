# coding=utf8
# Copyright (c) 2018 CineUse

from flask_restplus import Namespace


hook_ns = Namespace('git_hook', description='post from github/gitee web hooks.')
