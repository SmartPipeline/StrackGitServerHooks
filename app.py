from flask import Flask
from flask_restful import reqparse, Api, Resource
import json
from strack_api.strack import Strack

app = Flask(__name__)
api = Api(app)

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

# 初始化st对象
st = Strack('http://129.204.29.79:88/strack', 'gitee', 'gitee2Strack')


class GiteePR(Resource):

    def post(self):
        # 解析payload
        args = parser.parse_args()
        #
        return args.get('action'), 201


api.add_resource(GiteePR, '/gitee_strack_desktop_pr')


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)
