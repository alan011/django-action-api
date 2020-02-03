import time
import sys
from os import path, makedirs


class Logger(object):
    level_define = {
        "DEBUG": 5,
        "INFO": 4,
        "WARNING": 3,
        "ERROR": 2,
        "FATAL": 1,
    }

    def __init__(self, log_file=sys.stdout, trigger_level='INFO', msg_prefix=None):
        self.log_file = log_file
        self.trigger_level = trigger_level
        self.pre_check()
        if log_file == sys.stdout:
            self.log_f_obj = sys.stdout
        else:
            try:
                self.log_f_obj = open(log_file, 'a')
            except Exception:
                self.log_f_obj = sys.stdout
        self.msg_prefix = msg_prefix

    def pre_check(self):
        if self.log_file == sys.stdout:
            return None
        log_dir = path.dirname(self.log_file)
        if not path.isdir(log_dir):
            makedirs(log_dir)

    def log(self, msg, level='INFO'):
        this_level = level.upper()
        msg = str(msg)
        msg = str(self.msg_prefix) + msg if self.msg_prefix is not None else msg
        if this_level in self.level_define and self.level_define[this_level] <= self.level_define[self.trigger_level.upper()]:
            log_time = time.strftime("%F %T", time.localtime(time.time()))
            log_line = ' '.join([log_time, f"[{level}]", msg])
            print(log_line, file=self.log_f_obj, flush=True)

    def exit(self, msg):
        level = 'FATAL'
        log_time = time.strftime("%F %T", time.localtime(time.time()))
        log_line = ' '.join([log_time, level, msg])
        raise SystemExit(log_line)
