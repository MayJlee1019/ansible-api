#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time   : 2018/12/16 14:00
# @Author : 
# @File   : ansible_playbook_api.py

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase


# 重写CallbackBase
class ResultsCollector(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        self.host_skipped = {}

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self.host_skipped[result._host.get_name()] = result


class Runner(object):

    def __init__(self, resource="/yun/yun/hosts", *args, **kwargs):
        """
           初始化Runner对象
        """
        self.resource = resource
        self.inventory = None
        self.variable_manager = None
        self.loader = None
        self.options = None
        self.passwords = None
        self.callback = None
        self.__initializeData()
        self.results_raw = {}

    def __initializeData(self):
        """
          初始化ansible
        """

        Options = namedtuple('Options', ['connection',
                                         'module_path',
                                         'forks',
                                         'timeout',
                                         'remote_user',
                                         'ask_pass',
                                         'private_key_file',
                                         'ssh_common_args',
                                         'ssh_extra_args',
                                         'sftp_extra_args',
                                         'scp_extra_args',
                                         'become',
                                         'become_method',
                                         'become_user',
                                         'ask_value_pass',
                                         'verbosity',
                                         'check',
                                         'listhosts',
                                         'listtasks',
                                         'listtags',
                                         'syntax',
                                         'diff'])

        self.options = Options(connection=connection,
                               module_path=module_path,
                               forks=forks,
                               timeout=timeout,
                               remote_user=remote_user,
                               ask_pass=False,
                               private_key_file=None,
                               ssh_common_args=None,
                               ssh_extra_args=None,
                               sftp_extra_args=None,
                               scp_extra_args=None,
                               become=become,
                               become_method=become_method,
                               become_user=become_user,
                               ask_value_pass=False,
                               verbosity=None,
                               check=False,
                               listhosts=False,
                               listtasks=False,
                               listtags=False,
                               syntax=False,
                               diff=False)

        self.loader = DataLoader()
        self.passwords = None
        self.inventory = InventoryManager(loader=self.loader, sources=self.resource)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def playbook_run(self, playbook_yml):
        """
         Playbook 方法
        """

        self.callback = ResultsCollector()
        playbook = PlaybookExecutor(playbooks=playbook_yml,
                                    inventory=self.inventory,
                                    variable_manager=self.variable_manager,
                                    loader=self.loader,
                                    options=self.options,
                                    passwords=self.passwords)
        playbook._tqm._stdout_callback = self.callback
        playbook.run()

    # 修改返回值
    def get_result(self):
        self.results_raw = {'success': {}, 'failed': {}, 'unreachable': {}, 'skipped': {}}
        for host, result in self.callback.host_ok.items():
            self.results_raw['success'][host] = result._result

        for host, result in self.callback.host_failed.items():
            self.results_raw['failed'][host] = result._result

        for host, result in self.callback.host_unreachable.items():
            self.results_raw['unreachable'][host] = result._result['msg']
        for host, result in self.callback.host_skipped.items():
            self.results_raw['skipped'][host] = result._result
        return self.results_raw


######################全局设置 #####################################
module_path = ['/yun/yun/bin/ansible']
# 获取本机的Ansible的路径： /yun/yun/bin/ansible

resource = ''
# 默认使用hosts文件

forks = 100
# 开启多少线程协助

timeout = 60
# 设置执行超时时间

remote_user = 'root'
# ansible远程到目标机器所用的用户

playbook_yml = ['/tmp/aa.yml']
# 定义playbook的位置
become = None
# 是否切换用户True、None

become_method = None
# 切换用户的方法： su sudo

become_user = None
# 切换到哪个用户，默认是不切换用户 可以在playbook里设置某条命令是否切换root/用户 执行，如果设置了就是所有的playbook都用root/用户 执行

connection = 'ssh'
# 连接方式 smart ,ssh
################################################################
def  main():
    Runner()


if __name__ == "__main__":
    main()

# if resource == '':
#   ansible = Runner()
#   ansible.playbook_run(playbook_yml)
#   print(json.dumps(ansible.get_result(), indent=4))
# else:
#   ansible = Runner(resource)
#   ansible.playbook_run(playbook_yml)
#   print(json.dumps(ansible.get_result(), indent=4))
