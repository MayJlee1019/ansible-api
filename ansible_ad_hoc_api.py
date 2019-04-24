#!/usr/bin/env python
# -*- coding:utf-8 -*-
#@Time   : 2018/12/16 13:59
#@Author : yun
#@File   : ansible_ad_hoc_api.py


import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.plugins.callback import CallbackBase
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager


# 重写CallbackBase
class ResultsCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        # 初始化这个对象
        super(ResultsCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result


class Runner(object):

    def __init__(self, *args, **kwargs):
        self.loader = DataLoader()
        self.results_callback = ResultsCallback()
        self.inventory = InventoryManager(loader=self.loader, sources=HOST_DIR)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.passwords = None
        self.results_raw = {}

        Options = namedtuple('Options',
                             ['connection',
                              'remote_user',
                              'ask_sudo_pass',
                              'verbosity',
                              'ack_pass',
                              'module_path',
                              'forks',
                              'become',
                              'become_method',
                              'become_user',
                              'check',
                              'listhosts',
                              'listtasks',
                              'listtags',
                              'syntax',
                              'sudo_user',
                              'sudo',
                              'diff'])
        # 初始化需要的对象
        self.options = Options(connection='ssh',
                               remote_user=None,
                               ack_pass=None,
                               sudo_user=None,
                               forks=10,
                               sudo='yes',
                               ask_sudo_pass=False,
                               verbosity=10,
                               module_path=None,
                               become=None,
                               become_method=None,
                               become_user=None,
                               check=False,
                               diff=False,
                               listhosts=None,
                               listtasks=None,
                               listtags=None,
                               syntax=None)

    #
    def run_ad_hoc(self):
        play_source = dict(
            name="Ansible Play ad-hoc",
            hosts='test',
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell', args='echo aaa > /tmp/b.txt'), register='shell_out'),
                # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback,
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

    ##修改返回值
    def get_result(self):
        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}}
        for host, result in self.results_callback.host_ok.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['success'][hostvisiable] = result._result

        for host, result in self.results_callback.host_failed.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['failed'][hostvisiable] = result._result

        for host, result in self.results_callback.host_unreachable.items():
            hostvisiable = host.replace('.', '_')
            self.results_raw['unreachable'][hostvisiable] = result._result
        return self.results_raw


######################此设置为   全局设置  请谨慎修改，推荐默认######################################
#
HOST_DIR = ['/yun/yun/hosts']

resource = ''
# 默认使用hosts文件


forks = 100
# 开启多少线程协助

timeout = 60
# 设置超时时间


remote_user = 'root'
# ansible远程到目标机器所用的用户

become = None
# 是否切换用户True、None

become_method = None
# 切换用户的方法： su sudo 取决于你是什么系统 测试环境:centos7.3 使用su


become_user = None
# 切换到哪个用户
# 默认是不切换用户 可以在playbook里设置某条命令是否切换root/用户 执行，如果设置了就是所有的playbook都用root


connection = 'ssh'
################################################################

if __name__ == "__main__":
    ansible = Runner()
    ansible.run_ad_hoc()
    print(json.dumps(ansible.get_result(), indent=4))
