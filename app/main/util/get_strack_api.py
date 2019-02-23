# coding=utf8
# Copyright (c) 2018 CineUse
from app.main.util.strack_api import Strack


def get_strack_api(base_url, login, passwd):
    return Strack(base_url, login, passwd)


if __name__ == "__main__":
    get_strack_api('http://129.204.29.79:88/strack', 'gitee', 'gitee2Strack')
