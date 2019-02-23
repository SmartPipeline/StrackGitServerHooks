# coding=utf8
# Copyright (c) 2018 CineUse
import os
import re
import sys
import time
import logging
import logging.handlers
from datetime import datetime
import tempfile


def get_logger(logger_name=None, level=logging.DEBUG,
               log_format='%(asctime)s - STRACK API - %(filename)s:%(lineno)s - %(message)s'):

    time_code = time.time()
    # LOG_FILE = os.path.join(os.environ.get("TMP"), 'STRACK_API_%s.log' % time_code)
    log_file = os.path.join(tempfile.gettempdir(), 'STRACK_API_%s.log' % time_code)

    if not logger_name:
        logger_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)  # 实例化handler

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(level)

    return logger


class FilterParser(object):

    GROUP = ["\(", "\)"]
    LOGIC = [" and ", " or "]
    OPERATORS = {
                ">": "-gt",
                ">=": "-egt",
                "<": "-lt",
                "<=": "-elt",
                "=": "-eq",
                "==": "-eq",
                "!=": "-neq",
                "in": "-in",
                "not in": "-not-in",
                "like": "-lk",
                "not like": "-not-lk",
                "between": "-bw",
                "not between": "-not-bw"
            }

    def parse(self, expression):
        # 元组转列表
        expression_str = self.tuple_to_list(expression)
        # 切分并解析
        pattern = "(" + "|".join(self.LOGIC + self.GROUP) + ")"
        ex_list = re.split(pattern, expression_str)
        if len(ex_list) == 1:
            return self.__exp_to_dict(ex_list[0])
        return self.make_filter(ex_list)

    def tuple_to_list(self, exp_str):
        # - 找出最内层小括号
        inner_str_list = re.findall('\([^()]*\)', exp_str)

        def filter_tuples(s):
            for logic in self.LOGIC:
                if logic in s:
                    return False
            return True

        tuples = filter(filter_tuples, inner_str_list)
        lists = map(lambda tpl: re.sub("\((.*)\)", "[\g<1>]", tpl), tuples)     # 从tuple样式的字符串求出list样式字符串
        # - 将括号内容不带logic的替换成中括号
        for tpl, lst in zip(tuples, lists):
            exp_str = exp_str.replace(tpl, lst)
        return exp_str

    def make_filter(self, ex_list):
        ex_list = [i for i in ex_list if i not in [" ", ""]]
        last_condition = None
        filter_dict = {}
        for i in range(len(ex_list)):
            # 因为循环中会动态删除,所以要防止index超限
            if i >= len(ex_list):
                break
            if ex_list[i] in self.LOGIC:
                logic = ex_list[i]
                filter_dict["_logic"] = logic.strip()
                if not last_condition:
                    last_condition = ex_list[i-1]
                # 条件是dict 则为 {"0": {条件}}
                if isinstance(last_condition, dict):
                    filter_dict["0"] = last_condition
                # 否则，则为{“字段”：[“关系”， “值”]}
                else:
                    condition_dict = self.__exp_to_dict(last_condition)
                    filter_dict = self.append_condition(filter_dict, condition_dict, logic)
                # 遇“（”则递归
                if ex_list[i+1] == "(":
                    right_index = i + ex_list[i:].index(")")
                    filter_dict["1"] = self.make_filter(ex_list[i+1:right_index])
                    del ex_list[i+1:right_index]
                else:
                    new_condition_dict = self.__exp_to_dict(ex_list[i+1])
                    filter_dict = self.append_condition(filter_dict, new_condition_dict, logic)
                last_condition = filter_dict
                filter_dict = {}
        return last_condition

    def __exp_to_dict(self, exp_str):
        if not exp_str:
            return {}
        pattern = "(" + "|".join(self.OPERATORS.keys()) + ")"
        exp_list = re.split(pattern, exp_str)
        if len(exp_list) == 5:
            exp_list = [exp_list[0], exp_list[1]+exp_list[3], exp_list[4]]
        if len(exp_list) == 3:
            key_str = exp_list[0].strip()
            operator_str = self.OPERATORS.get(exp_list[1])
            value_str = self.reformat_time_list(exp_list[2].strip())
            # list_str to list
            if (value_str[0], value_str[-1]) == ("[", "]"):
                value_str = value_str[1: -1]
            # clear space in list
            value_str = re.sub("\s*,\s*", ",", value_str)
            return {key_str: [operator_str, value_str]}
        else:
            raise ValueError("invalid expression")

    @staticmethod
    def append_condition(filter_dict, condition_dict, logic):
        condition_key = condition_dict.keys()[0] if condition_dict else None
        if not condition_key:
            return filter_dict
        if condition_key in filter_dict:
            condition_dict[condition_key] = [condition_dict.get(condition_key), filter_dict.get(condition_key), logic]
        return dict(filter_dict.items() + condition_dict.items())

    def reformat_time_list(self, value_str):
        if value_str.count(",") == 1:
            new_values = []
            str_list = value_str.split(",")
            for i in str_list:
                m = re.match(r"`(\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?|(now))`", i.strip())
                if m:
                    if m.groups()[1] or m.groups()[0] == "now":
                        match_time = m.groups()[0]
                    else:
                        match_time = "%s 00:00:00" % m.groups()[0]
                    new_values.append(str(self.time_to_stamp(match_time)))
                else:
                    new_values.append(i)
            value_str = ",".join(new_values)
        return value_str

    @staticmethod
    def time_to_stamp(time_str):
        if time_str == "now":
            input_time = datetime.now()
        else:
            input_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        epoch = datetime(1970, 1, 1)
        time_d = input_time - epoch
        time_stamp = (time_d.microseconds + (time_d.seconds + time_d.days * 86400) * 10**6) / 10**6
        return int(time_stamp)


if __name__ == "__main__":
    # ex = "first_name = cheng and dept_id = 7 and (user_id != 147 or user_email in comp@.com or user_login like comp)"
    ex = "artist.name = zhangsan"    # -> "id in 1,2,3,4,5"
    # ex = "first_name== cheng"
    # ex = "(user_email like strack or user_email = caochen@vhq.com) and " \
    #      "(dept_id = 4 or dept_id > 20) and user_status = 10"
    parser = FilterParser()
    print(parser.parse(ex))
    # print("{'project_id': ['-eq', 15]}")
    # print ex
    # print tuple_to_list(s)
