import os
import json
from django.conf import settings
from threading import Thread


class CmdJob(object):
    def __init__(self, cmd="", task_name=None):
        self.cmd = cmd
        self.task_name = task_name
        self.result = {}


class AnsibleRunner(object):
    def __init__(self, ansible_root, ansible_bin, ansible_key, timeout=60, quiet=False, parallel=False):
        self.ansible_root = ansible_root
        self.bin = ansible_bin
        self.key = ansible_key
        self.jobs = []
        self.timeout = timeout
        self.port = 22 if getattr(settings, 'ANSIBLE_SSH_PORT', None) is None else settings.ANSIBLE_SSH_PORT
        self.quiet = quiet
        self.parallel = parallel

    def add_job(self, task_name, playbook, hosts, vars=None, single_file_playbook=False):
        # To check playbook.
        if single_file_playbook:
            if not playbook.startswith('/'):
                raise Exception("AnsibleRunner.add_job(): Path of single file playbook should not be relatively.")
            _playbook = playbook
        else:
            _playbook = os.path.join(self.ansible_root, playbook)
        if not os.path.isfile(_playbook):
            raise Exception(f"AnsibleRunner.add_job(): Playbook '{_playbook}' not found.")

        # To check target hosts
        _hosts = ','.join(hosts)
        if not _hosts:
            raise Exception("AnsibleRunner.add_job(): No target hosts provided.")

        # To check vars and generate ansible command.
        if vars:
            _vars = json.dumps(vars)
            job = CmdJob(
                f"{self.bin} -i {_hosts}, -e \'{_vars}\' {_playbook} --private-key={self.key} -T {self.timeout} --ssh-extra-args \'-p {self.port}\'",
                task_name=task_name
            )
        else:
            job = CmdJob(
                f"{self.bin} -i {_hosts}, {_playbook} --private-key={self.key} -T {self.timeout} --ssh-extra-args \'-p {self.port}\'",
                task_name=task_name
            )

        # To add job.
        self.jobs.append(job)

    def ansible_result_parser(self, job, lines):
        """
        To parse ansible result to a dict, with items like:
        {
            "192.168.1.2": {"result":"success", "log_lines": [...]},
            "192.168.1.3": {"result":"failed", "log_lines": [...]},
        }
        """

        # To remove playbook retry line, when ansible-playbook runs failed.
        _i = None
        for line in filter(lambda l: l.strip().endswith(".retry"), lines):
            _i = lines.index(line)
            break
        if _i is not None:
            lines.pop(_i)

        # The rest of lines should be a valid json.
        str_result = ''.join(lines)
        if not self.quiet:
            print(str_result)
        try:
            ansible_result = json.loads(str_result)
        except Exception:
            # To store the string value as result, if not a json.
            job.result = str_result
        else:
            if not self.quiet:
                print("===> json load succeeded!")
            for task_result in filter(lambda t: t['task']['name'] == job.task_name, ansible_result['plays'][0]['tasks']):
                # print(task_result)
                for host_ip in task_result['hosts'].keys():
                    job.result[host_ip] = {"result": "success", "log_lines": []}
                    if task_result["hosts"][host_ip].get('failed') or task_result["hosts"][host_ip].get('unreachable'):  # Tag failed.
                        job.result[host_ip]["result"] = 'failed'
                    _stdout = task_result["hosts"][host_ip].get("stdout_lines", [])
                    _stderr = task_result["hosts"][host_ip].get("stderr_lines", [])
                    job.result[host_ip]["log_lines"] = _stdout + _stderr
                break

    def do_job(self, job):
        """
        To run a single job.
        """
        if not self.quiet:
            print(f"===> {job.cmd}")
        print(job.cmd)
        with os.popen(job.cmd) as f:
            self.ansible_result_parser(job, f.readlines())

    def go(self):
        """
        Start to run all jobs.
        """
        print(self.jobs)
        if self.parallel:
            pool = []
            for job in self.jobs:
                pool.append(Thread(target=self.do_job, args=[job]))
                print('lalala')
            for p in pool:
                p.start()
            for p in pool:
                p.join()
        else:
            for job in self.jobs:
                self.do_job(job)
