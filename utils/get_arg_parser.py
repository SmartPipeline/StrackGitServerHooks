# coding=utf8
# Copyright (c) 2018 CineUse

from flask_restplus import reqparse, Api, Resource


def get_arg_parser(args_list):
    parser = reqparse.RequestParser()
    for arg_dict_item in args_list:
        arg_name = arg_dict_item.get('name')
        arg_dict_item.pop('name')
        parser.add_argument(arg_name, **arg_dict_item)
    return parser


if __name__ == "__main__":
    get_arg_parser([])
