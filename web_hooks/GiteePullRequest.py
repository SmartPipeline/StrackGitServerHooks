# coding=utf8
# Copyright (c) 2019 CineUse

from flask_restful import reqparse, Resource


parser = reqparse.RequestParser()
parser.add_argument('action', type=str)
parser.add_argument('pull_request', type=dict)
parser.add_argument('number', type=int)
parser.add_argument('iid', type=int)
parser.add_argument('title', type=str)
parser.add_argument('state', type=str)
parser.add_argument('merge_status', type=str)
parser.add_argument('merge_commit_sha', type=str)
parser.add_argument('url', type=str)
parser.add_argument('source_branch', type=str)
parser.add_argument('source_repo', type=dict)
parser.add_argument('target_branch', type=str)
parser.add_argument('target_repo', type=dict)
parser.add_argument('project', type=dict)
parser.add_argument('repository', type=dict)
parser.add_argument('author', type=dict)
parser.add_argument('updated_by', type=dict)
parser.add_argument('sender', type=dict)
parser.add_argument('target_user', type=dict)
parser.add_argument('hook_name', type=str)
parser.add_argument('password', type=str)


class GiteePullRequest(Resource):
    st = None
    password = None

    def post(self):
        # 解析payload
        args = parser.parse_args()
        #
        return args.get('action'), 201


if __name__ == "__main__":
    GiteePullRequest()
