import logging

from fex.exceptions import ConfigError


class Configurator:

    def __init__(self):
        self._fex_actions = {
            'upload': '_upload',
            'own_object_id': 'own_objects',
            'is_list_dirs': 'list_folders',
            'object_id_info': 'print_object_info',
            'is_list_objects': 'list_objects'
        }
        self.log = logging.getLogger(self.__class__.__name__)

    def configure(self, obj):
        do_login = self._process_login(obj)
        action = self._process_actions(obj)
        return do_login, action

    @staticmethod
    def _process_login(obj):
        if obj.username and obj.password:
            do_login = True
        elif obj.is_anonymous or obj.object_id_info or obj.is_list_dirs:
            do_login = False
        else:
            raise ConfigError('Bad login arguments, please verify')

        return do_login

    def _process_actions(self, obj):
        # TODO: Refactor this.
        if obj.own_object_id:
            action = self._fex_actions['own_object_id']
        elif obj.object_id_info:
            action = self._fex_actions['object_id_info']
        elif obj.is_list_dirs:
            action = self._fex_actions['is_list_dirs']
        elif obj.is_list_objects:
            action = self._fex_actions['is_list_objects']
        else:
            action = self._fex_actions['upload']

        return action
