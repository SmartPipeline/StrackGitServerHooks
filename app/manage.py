# coding=utf8
# Copyright (c) 2019 CineUse
import os
import unittest

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app.main import create_app, db
from app import blueprint

# 导入models以便于数据库迁移（Migrate）
from app.main.model import user
from app.main.model import blacklist

# 环境变量'BOILERPLATE_ENV'可以被设置为dev, prod, test中的一个
app = create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
app.register_blueprint(blueprint)

# 推送app实例给各个context
app.app_context().push()

manager = Manager(app)

migrate = Migrate(app, db)

# 使用MigrateCommand可以使用Flask-Script的迁移命令来迁移数据库
manager.add_command('db', MigrateCommand)


@manager.command
def run():
    app.run()


@manager.command
def test():
    """Runs the unit tests."""
    tests = unittest.TestLoader().discover('test', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()
