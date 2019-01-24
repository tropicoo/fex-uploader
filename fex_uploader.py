#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

from fex.api import Api
from fex.configurator import Configurator
from fex.constants import HOST
from fex.printer import Printer
from fex.uploader import Uploader
from fex.exceptions import UserLoginError, OwnObjectError
from fex.object import Object
from fex.utils import convert_size


class Fex:
    def __init__(self):
        args = self.parse_args()
        self._obj = Object(args)
        self._api = Api(obj=self._obj)
        self._printer = Printer(obj=self._obj)
        self._upload = Uploader(api=self._api, printer=self._printer,
                               obj=self._obj).upload
        self._configurator = Configurator()
        self._host = 'https://{0}'.format(HOST)
        self._log = logging.getLogger(self.__class__.__name__)

    def run(self):
        self._log.debug(
            'Listing object\'s attributes: {0}'.format(vars(self._obj)))
        login, action = self._configurator.configure(self._obj)

        if login:
            self._login()

        fex_method = getattr(self, action)
        fex_method()

    def _login(self):
        if self._obj.is_force:
            self._log.info('Force login')
            self._api.purge_cookies()

        if not self._api.process_cookies():
            self._log.debug('Trying to log in')
            credentials = {'login': self._obj.username,
                           'password': self._obj.password}
            login_response = self._api.get_signin(data=credentials)
            login_state, login_msg = self._verify_login(login_response)

            if login_state:
                self._log.info('\n'.join(login_msg))
                self._api.save_cookies()
            else:
                raise UserLoginError('\n'.join(login_msg))

    def _verify_login(self, response):
        # TODO: Refactor control flag; raise on non-successful
        return_state = False

        if response.get('result') \
                and (response.get('login') == self._obj.username
                     or response.get('user', 0).get(
                    'login') == self._obj.username):
            msg = ['Login successful']
            return_state = True
        elif not response.get('result') \
                and not response.get('captcha'):
            msg = ['Authentication error, check credentials',
                   'Response data: {0}'.format(response.text),
                   'Cookies: {0}'.format(response.cookies)]
        elif response.get('captcha'):
            msg = ['Authentication error, captcha request',
                   'Response data: {0}'.format(response.text)]
        elif not response.get('result') \
                and len(response.keys()) == 1:
            msg = ['Are you uploading to non-existing Object ID?',
                   'Response data: {0}'.format(response.text)]
        else:
            msg = ['Can\'t verify login due to an unknown error',
                   'Response data: {0}'.format(response.text)]

        return return_state, msg

    def own_objects(self, **kwargs):
        object_ids = kwargs.get('own_object_id')
        view_password = kwargs.get('view_password')
        msgs = []
        got_view = False

        for object_id in object_ids:
            self._log.info('Owning object {0}'.format(object_id))
            if view_password and not got_view:
                self._api.get_object_view(object_id,
                                         view_password=view_password)
                msgs.append(['Object password', '{0}'.format(view_password)])
                got_view = True

            r = self._api.get_object_own(object_id)

            if r.get('result'):
                msgs.extend(
                    [['Object {0}'.format(object_id), 'Successfully owned'],
                     ['Object URL', '{0}/#!{1}'.format(self._host, object_id)],
                     ['Owner', '{0}'.format(self._obj.username)]])
                self._printer.print_on_complete(msgs)
            else:
                raise OwnObjectError(
                    'Own failed for object {0}'.format(object_id))

    def print_object_info(self, **kwargs):
        object_ids = kwargs.get('object_id_info')
        view_password = kwargs.get('view_password')
        msgs = []

        for object_id in object_ids:
            view_response = self._api.get_object_view(object_id,
                                                     view_password=view_password)

            if view_password:
                msgs.append(
                    'Object password       : {0}'.format(view_password))

            if view_response.get('result'):
                for k, v in view_response.items():
                    msgs.append('{0}: {1}'.format(k, v))
                msgs.append(
                    'Object URL            : {0}/#!{1}'.format(self._host,
                                                               object_id))
                self._printer.print_on_complete(msgs)
            else:
                print('Can\'t get info, wrong password?')

    def list_folders(self, **kwargs):
        object_id = kwargs.get('object_id')
        view_password = kwargs.get('view_password')
        self._api.process_cookies()

        view_response = self._api.get_object_view(object_id,
                                                 view_password=view_password)

        if view_response.get('result'):
            upload_list = view_response.get('upload_list')
            self._log.info('Fetching data and building folder list...')
            folders = self._process_list(upload_list)
            self._printer.print_on_complete(folders,
                                           headers=['Folder name', 'ID',
                                                    'Path'],
                                           showindex=[x + 1 for x in
                                                      range(len(folders))])
        else:
            self._log.error(
                'Can\'t get info, wrong password or private object?')

    def list_objects(self):
        response = self._api.get_home()
        objects_list = response.get('object_list')
        objects = [(obj.get('preview'),
                    obj.get('token'),
                    obj.get('login'),
                    convert_size(int(obj.get('upload_size', 0))),
                    (False, True)[obj.get('public', 0)],
                    (False, True)[obj.get('with_view_pass')],
                    (False, True)[obj.get('can_edit', 0)],
                    time.ctime(obj.get('create_time', 0)),
                    ) for obj in objects_list]

        headers = ['Name', 'ID', 'Owner', 'Object size', 'Public', 'Password',
                   'Editable', 'Created on']
        self._printer.print_on_complete(objects, headers=headers)

    def _process_list(self, upload_list, dirs=None, parent_folder=None):
        if dirs is None:
            dirs = []
        if parent_folder is None:
            parent_folder = []
        # folder_list_url = '{0}{1}{2}'.format(HOST, API_METHODS['object_folder_list'], self.object_id)

        for elem in upload_list:
            if elem.get('is_folder'):
                folder_id = elem.get('upload_id')
                parent_folder.append(folder_id)
                base_parent_folder = parent_folder[:-1]

                # folder_view_url = '{0}{1}{2}/{3}'.format(HOST, API_METHODS['object_folder_view'],
                #                                      self.object_id, folder_id)
                # folder_view_r = self.s.post(folder_view_url)
                # folder_view_r.raise_for_status()
                folder_view_r = self._api.get_object_folder_view(
                    folder_id=folder_id)
                folder_view_r = folder_view_r.json()

                parent_folder_ids = {'list': ','.join(parent_folder)}
                # folder_list_r = self.s.post(folder_list_url, data=parent_folder_ids)
                # folder_list_r.raise_for_status()
                folder_list_r = self._api.get_object_folder_list(
                    data=parent_folder_ids)
                folder_list_r = folder_list_r.json()
                folder_list = folder_list_r.get('folder_list')
                folder_list = [elem.get('name') for elem in folder_list]
                dirs.append((elem.get('name'), elem.get('upload_id'),
                             ' \u2192 '.join(folder_list)))
                self._log.info('Found folders {0}\r'.format(len(dirs)), end='')
                if sys.platform != 'win32':
                    sys.stdout.write("\033[K")

                self._process_list(folder_view_r.get('upload_list'), dirs,
                                   parent_folder)
                parent_folder = base_parent_folder

        dirs = sorted(dirs, key=lambda x: x[2].lower())
        return dirs

    def parse_args(self):
        # TODO: Move back to '__main__'
        parser = argparse.ArgumentParser(description='FEX.net uploader')
        group = parser.add_argument_group('user upload')
        parser.add_argument('-a', '--anonymous', action='store_true',
                            default=False,
                            dest='is_anonymous',
                            help='upload anonymously')
        group.add_argument('-u', '--user', action='store', dest='username',
                           help='set a username')
        group.add_argument('-p', '--password', action='store', dest='password',
                           help='set a password')
        parser.add_argument('-s', '--secret', action='store', dest='secret',
                            help='set a password for an object')
        parser.add_argument('--hint', action='store', dest='hint',
                            help='set a password hint for an object')
        group.add_argument('-o', '--object', action='store', dest='object_id',
                           help='set an object id')
        group.add_argument('-f', '--file', action='store', dest='file_list',
                           help='file name(s)', nargs='+')
        parser.add_argument('--view-password', action='store',
                            dest='view_password',
                            help='object\'s password')
        parser.add_argument('--object-name', action='store',
                            dest='object_name',
                            help='object\'s name')
        parser.add_argument('--object-description', action='store',
                            dest='object_description',
                            help='object\'s description')
        parser.add_argument('-d', '--dir', action='store', dest='dir_path',
                            help='take files from directory')
        parser.add_argument('--force', action='store_true', default=False,
                            dest='is_force',
                            help='force login')
        parser.add_argument('--verify', action='store_true', default=False,
                            dest='is_verify',
                            help='verify checksums')
        parser.add_argument('--own', action='store', dest='own_object_id',
                            help='inherit object', nargs='+')
        parser.add_argument('--folder-create', action='store',
                            dest='folder_create',
                            help='create folder with name')
        parser.add_argument('--folder', action='store', dest='folder_id',
                            help='upload to folder id')
        parser.add_argument('--list-dirs', action='store_true', default=False,
                            dest='is_list_dirs',
                            help='list folders for object')
        parser.add_argument('--list-objects', action='store_true',
                            default=False, dest='is_list_objects',
                            help='list objects')
        parser.add_argument('--public', default=None,
                            choices=('true', 'false'), dest='public',
                            help='make object public or private, default true')
        parser.add_argument('--info', action='store', dest='object_id_info',
                            help='print object info', nargs='+')
        parser.add_argument('--version', action='version',
                            version='%(prog)s 0.1')

        args = parser.parse_args()
        args_dict = vars(args)

        if not len(sys.argv) > 1:
            parser.print_help()
            sys.exit(1)

        return args_dict


if __name__ == '__main__':
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    file_handler = logging.FileHandler(
        '{0}.log'.format(os.path.splitext(os.path.basename(__file__))[0]))
    file_handler.setFormatter(logging.Formatter(log_format))

    fex = Fex()
    fex.run()
