from helpers.vmnf_helpers import VimanaHelp
from res.vmnf_banners import s4dhu0nv1m4n4

require_module = [
    'args', 'run', 'info', 'guide'
]

vmnf_cmds = {
    'about':  s4dhu0nv1m4n4(True),
    'args' :  VimanaHelp.args.__doc__,
    'guide':  VimanaHelp.guide.__doc__,
    'flush':  VimanaHelp.flush.__doc__,
    'info' :  VimanaHelp.info.__doc__,
    'list' :  VimanaHelp.list.__doc__,
    'load' :  VimanaHelp.list.__doc__,
    'run'  :  VimanaHelp.run.__doc__,
    'start':  VimanaHelp.start.__doc__
}

class vfACK:
    def __init__(self, **_vfh_):
        self._vfh_ = _vfh_

    def tatic_mode(self):
        return False if (
            not self._vfh_['session_mode'] \
            and not self._vfh_['listener_mode'] \
            and not self._vfh_['auth_mode'] \
            and not self._vfh_['target_url'] \
            and not self._vfh_['framework_search_version']
        ) else True

    def default_guide_mode(self):
        return True if (
            not self._vfh_['guide_examples'] \
            and not self._vfh_['guide_args'] \
            and not self._vfh_['guide_labs']
        ) else False

    def is_target_set(self):
        return True if (
            self._vfh_['single_target'] \
            or self._vfh_['file_scope'] \
            or self._vfh_['ip_range'] \
            or self._vfh_['cidr_range'] \
            or self._vfh_['list_target'] 
        ) else False

    def version_search(self):
        return True if (
            self._vfh_['django_version'] \
            or self._vfh_['flask_version'] \
            or self._vfh_['tornado_version'] \
            or self._vfh_['web2py_version']
        ) else False

    def exec_enabled(self):
        return True if (
            self._vfh_['save_case'] \
            and self._vfh_['exec_case'] 
            ) else False

