# coding=utf8
# Copyright (c) 2018 CineUse


def clear_empty_args(arg_dict):
    for key, value in arg_dict.items():
        # pre-process
        if isinstance(value, str):
            value = value.strip()
        if not value:
            arg_dict.pop(key)

    return arg_dict


def parse_args(parser):
    all_args = parser.parse_args()
    return clear_empty_args(all_args)


if __name__ == "__main__":
    parse_args()
