#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time

import fex.exceptions
from fex.api import API
from fex.constants import HOST
from fex.printer import Printer
from fex.uploader import Uploader
from fex.utils import convert_size


class Fex:
    def __init__(self, arguments):
        self._log = logging.getLogger(self.__class__.__name__)
        self._obj = arguments
        self._api = API()
        self._api.initialize_cookies(self._obj.username)
        self._printer = Printer(obj=self._obj)
        self._uploader = Uploader(api=self._api, printer=self._printer,
                                obj=self._obj)

    def run(self):
        self._log.debug('Listing object\'s '
                        'attributes: {0}'.format(vars(self._obj)))
        if self._obj.username and self._obj.password:
            self._login()
        elif not self._obj.is_anonymous or self._obj.object_id_info or \
                self._obj.is_list_dirs:
            raise fex.exceptions.ConfigError('Bad login arguments, please verify')

        if self._obj.own_object_id:
            self._own_objects()
        # elif self._obj.object_id_info:
        #     self._print_object_info()
        # elif self._obj.is_list_dirs:
        #     self._list_folders()
        # elif self._obj.is_list_objects:
        #     self._list_objects()
        else:
            self._uploader.upload()

    def _login(self):
        try:
            self._api.login(username=self._obj.username,
                            password=self._obj.password,
                            force=self._obj.is_force)
        except fex.exceptions.UserLoginError as err:
            sys.exit(str(err))

    def _own_objects(self):
        msgs = []
        if self._obj.view_password:
            self._api.get_object_view(self._obj.own_object_id[0],
                                      view_password=self._obj.view_password)
            msgs.append(['Object password', '{0}'.format(self._obj.view_password)])
        for object_id in self._obj.own_object_id:
            try:
                self._log.info('Owning object {0}'.format(object_id))
                self._api.get_object_own(object_id)
                msgs.extend(
                    [['Object {0}'.format(object_id), 'Successfully owned'],
                     ['Object URL', '{0}/#!{1}'.format(HOST, object_id)],
                     ['Owner', '{0}'.format(self._obj.username)]])
                self._printer.print_mesasge(msgs)
            except fex.exceptions.OwnObjectError as err:
                sys.exit(str(err))

    # def _print_object_info(self, object_id_info, view_password=None):
    #     msgs = []
    #
    #     for object_id in object_id_info:
    #         if view_password:
    #             msgs.append('Object password       : {0}'.format(view_password))
    #         view_response = self._api.get_object_view(object_id, view_password)
    #
    #
    #         if view_response.get('result'):
    #             for k, v in view_response.items():
    #                 msgs.append('{0}: {1}'.format(k, v))
    #             msgs.append('Object URL            : {0}/#!{1}'.format(self._host,
    #                                                            object_id))
    #             self._printer.print_on_complete(msgs)
    #         else:
    #             print('Can\'t get info, wrong password?')

    # def _list_folders(self, object_id, view_password):
    #     self._api.process_cookies()
    #     view_response = self._api.get_object_view(object_id,
    #                                              view_password=view_password)
    #     if view_response.get('result'):
    #         upload_list = view_response.get('upload_list')
    #         self._log.info('Fetching data and building folder list...')
    #         folders = self._process_list(upload_list)
    #         self._printer.print_on_complete(folders,
    #                                        headers=['Folder name', 'ID',
    #                                                 'Path'],
    #                                        showindex=[x + 1 for x in
    #                                                   range(len(folders))])
    #     else:
    #         self._log.error(
    #             'Can\'t get info, wrong password or private object?')
    #
    # def _list_objects(self):
    #     objects_list = self._api.get_home()
    #     objects = [(obj.get('preview'),
    #                 obj.get('token'),
    #                 obj.get('login'),
    #                 convert_size(int(obj.get('upload_size', 0))),
    #                 (False, True)[obj.get('public', 0)],
    #                 (False, True)[obj.get('with_view_pass')],
    #                 (False, True)[obj.get('can_edit', 0)],
    #                 time.ctime(obj.get('create_time', 0)),
    #                 ) for obj in objects_list]
    #
    #     headers = ['Name', 'ID', 'Owner', 'Object size', 'Public', 'Password',
    #                'Editable', 'Created on']
    #     self._printer.print_on_complete(objects, headers=headers)
    #
    # def _process_list(self, upload_list, dirs=None, parent_folder=None):
    #     if dirs is None:
    #         dirs = []
    #     if parent_folder is None:
    #         parent_folder = []
    #     # folder_list_url = '{0}{1}{2}'.format(HOST, API_METHODS['object_folder_list'], self.object_id)
    #
    #     for elem in upload_list:
    #         if elem.get('is_folder'):
    #             folder_id = elem.get('upload_id')
    #             parent_folder.append(folder_id)
    #             base_parent_folder = parent_folder[:-1]
    #
    #             # folder_view_url = '{0}{1}{2}/{3}'.format(HOST, API_METHODS['object_folder_view'],
    #             #                                      self.object_id, folder_id)
    #             # folder_view_r = self.s.post(folder_view_url)
    #             # folder_view_r.raise_for_status()
    #             folder_view_r = self._api.get_object_folder_view(
    #                 folder_id=folder_id)
    #             folder_view_r = folder_view_r.json()
    #
    #             parent_folder_ids = {'list': ','.join(parent_folder)}
    #             # folder_list_r = self.s.post(folder_list_url, data=parent_folder_ids)
    #             # folder_list_r.raise_for_status()
    #             folder_list_r = self._api.get_object_folder_list(
    #                 data=parent_folder_ids)
    #             folder_list_r = folder_list_r.json()
    #             folder_list = folder_list_r.get('folder_list')
    #             folder_list = [elem.get('name') for elem in folder_list]
    #             dirs.append((elem.get('name'), elem.get('upload_id'),
    #                          ' \u2192 '.join(folder_list)))
    #             self._log.info('Found folders {0}\r'.format(len(dirs)), end='')
    #             if sys.platform != 'win32':
    #                 sys.stdout.write("\033[K")
    #
    #             self._process_list(folder_view_r.get('upload_list'), dirs,
    #                                parent_folder)
    #             parent_folder = base_parent_folder
    #
    #     dirs = sorted(dirs, key=lambda x: x[2].lower())
    #     return dirs


if __name__ == '__main__':
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)
    file_handler = logging.FileHandler(
        '{0}.log'.format(os.path.splitext(os.path.basename(__file__))[0]))
    file_handler.setFormatter(logging.Formatter(log_format))

    parser = argparse.ArgumentParser(description='FEX.net uploader')
    group = parser.add_argument_group('user upload')
    parser.add_argument('-a', '--anonymous', action='store_true', # works
                        default=False,
                        dest='is_anonymous',
                        help='upload anonymously')
    group.add_argument('-u', '--user', action='store', dest='username', # works
                       help='set a username')
    group.add_argument('-p', '--password', action='store', dest='password', # works
                       help='set a password')
    parser.add_argument('-s', '--secret', action='store', dest='secret', # works
                        help='set a password for an object')
    parser.add_argument('--hint', action='store', dest='hint', # works
                        help='set a password hint for an object')
    parser.add_argument('--folder_name', action='store', dest='folder_name', # N/A
                        help='folder name to be created')
    group.add_argument('-o', '--object', action='store', dest='object_id', # works
                       help='set an object id')
    group.add_argument('-f', '--file', action='store', dest='file_list', # works
                       help='file name(s)', nargs='+')
    parser.add_argument('--view-password', action='store', # ????????????????????
                        dest='view_password',
                        help='object\'s password')
    # ABSENT
    parser.add_argument('--object-name', action='store',
                        dest='object_name',
                        help='object\'s name')
    # ABSENT
    parser.add_argument('--object-description', action='store',
                        dest='object_description',
                        help='object\'s description')
    parser.add_argument('-d', '--dir', action='store', dest='dir_path', # works +=
                        help='recursive upload of directory')
    parser.add_argument('--force', action='store_true', default=False, # works
                        dest='is_force',
                        help='force login')
    # Commented out since printer class is too
    # parser.add_argument('--verify', action='store_true', default=False,
    #                     dest='is_verify',
    #                     help='verify checksums')
    parser.add_argument('--own', action='store', dest='own_object_id', # works
                        help='inherit object', nargs='+')
    parser.add_argument('--folder-create', action='store', # not implemented
                        dest='folder_create',
                        help='create folder with name')
    parser.add_argument('--folder', action='store', dest='folder_id', # works
                        help='upload to existent folder id, object id required')
    parser.add_argument('--list-dirs', action='store_true', default=False,
                        dest='is_list_dirs',
                        help='list folders for object')
    # parser.add_argument('--list-objects', action='store_true', # n/a printer off
    #                     default=False, dest='is_list_objects',
    #                     help='list objects')
    parser.add_argument('--public', default=None, # works
                        choices=('true', 'false'), dest='public',
                        help='make object public or private, default true')
    # parser.add_argument('--info', action='store', dest='object_id_info',
    #                     help='print object info', nargs='+')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 0.1')

    args = parser.parse_args()
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(1)

    fex = Fex(args)
    fex.run()
