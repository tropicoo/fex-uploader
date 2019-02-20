import logging
import ntpath
import os
import sys

from requests_toolbelt import (MultipartEncoder, MultipartEncoderMonitor)

from fex.utils import convert_size, calculate_crc32, calculate_sha1


class Uploader:
    def __init__(self, api, printer, obj):
        self._api = api
        self._printer = printer
        self._obj = obj
        self._log = logging.getLogger(self.__class__.__name__)

    def upload(self, **kwargs):
        secret_set = False

        # create new object if self._obj.object_id == None (for anonymous too)
        # or get upload server
        if (self._obj.is_anonymous and not self._obj.object_id) or not self._obj.object_id:
            self._log.info('Object ID not provided, creating new')
            upload_server, self._obj.object_id = self._object_create()
            self._log.info('Created Object ID: {0}'.format(self._obj.object_id))
        else:
            upload_server, view_response, msg = self._get_upload_server(
                self._obj.view_password)
            self._log.debug(
                'Uploader server: {0}, view response: {1}, msg: {2}'.format(
                    upload_server, view_response, msg))
            # verify that upload server was returned
            if not isinstance(upload_server, str):
                if 'msg' in locals():
                    self._log.error(msg)
                sys.exit('upload_server wasn\'t returned')
        if 'view_response' not in locals() or not view_response:
            view_response = self._api.get_object_view(
                view_password=self._obj.view_password,
                object_id=self._obj.object_id)

        if self._obj.public:
            result = self._set_object_permissions(self._obj.public,
                                                  view_response.get('public'))

        # if folder name was provided, create a folder inside the object and return folder_id

        if self._obj.folder_name and not self._obj.folder_id:
            self._log.debug('Folder name: {0}'.format(self._obj.folder_name))
            folder_id = self._folder_create(self._obj.folder_name)

        upload_url = '/'.join([upload_server, self._obj.object_id])

        if self._obj.folder_id:
            upload_url = '/'.join([upload_url, self._obj.folder_id])

        if self._obj.dir_path:
            self._log.debug(
                'Using dir_path: {0}, folder id: {1}, upload server: {2}'.format(
                    self._obj.dir_path, self._obj.folder_id, upload_server))
            self.upload_dir_recursive(self._obj.dir_path, self._obj.folder_id,
                                      upload_server)
            return

        if not self._obj.file_list:
            return
        # upload file(s)
        for file in self._obj.file_list:
            uploaded = self._upload_file(file, upload_url)
            uploaded_json = uploaded.json()

            if not uploaded_json.get('result'):
                sys.exit('File {0} wasn\'t uploaded'.format(self.filename))

            self._log.info('Uploaded {0}'.format(self.filename))

            if self._obj.secret and not secret_set:
                if not self._set_password(self._obj.secret, self._obj.hint):
                    sys.exit('Password wasn\'t set, terminating..')
                secret_set = True

            parsed_object = self._printer._parse_object(
                uploaded=uploaded,
                view_response=view_response
            )
            self._printer.print_on_complete(parsed_object)

            if self._obj.is_verify:
                self._log.info('Verifying checksums...')
                args = self._verify_checksums(file, uploaded_json['sha1'],
                                              uploaded_json['crc32'])
                hashes = self._parse_hashes(args)
                parsed_hashes = self._process_hashes(hashes,
                                                     uploaded_json['sha1'],
                                                     uploaded_json['crc32'])
                self._printer.print_on_complete(parsed_hashes)

    def upload_dir_recursive(self, dir_path, folder_token, upload_server):
        folder_id = self._folder_create(self._path_leaf(dir_path),
                                        folder_token)
        folder_token = folder_id
        upload_url = '/'.join([upload_server, self._obj.object_id, folder_id])
        files, dirs = self._scan_dir(dir_path)

        self._log.info(
            'Found {0} files and {1} subdirs'.format(len(files), len(dirs)))

        for file in files:
            self._upload_file(file, upload_url)

        for subdir in dirs:
            self.upload_dir_recursive(subdir, folder_token, upload_server)

        r = self._api.get_object_view(object_id=self._obj.object_id)
        upload_count = r['upload_count']
        upload_size = convert_size(r['upload_size'])

        self._log.info(
            'Uploaded {0} files and folders, size: {1}'.format(upload_count,
                                                               upload_size))

    def _set_password(self, secret, hint):
        payload = {'pass': secret, 'pass_hint': hint}
        r = self._api.get_object_set_view_pass(data=payload,
                                              object_id=self._obj.object_id)
        return True if r.get('result') else False

    def _verify_checksums(self, file, sha1_server, crc32_server):
        sha1_local = calculate_sha1(file)
        crc32_local = calculate_crc32(file)
        sha1_state = (False, True)[sha1_local == sha1_server]
        crc32_state = (False, True)[crc32_local == crc32_server]
        return sha1_state, sha1_local, crc32_state, crc32_local

    def _object_create(self):
        return self._api.get_object_create()

    def _get_upload_server(self, view_password=None):
        res = self._api.get_object_view(view_password=view_password,
                                     object_id=self._obj.object_id)
        if res.get('can_edit'):
            upload_server = res.get('fs_upload')[0]
            return upload_server, res, None
        else:
            msg = 'You don\'t have permissions to upload to this Object'
            return None, None, msg

    # @staticmethod
    # def _parse_upload_server(r):
    #     return r.get('fs_upload')[0]

    def _set_object_permissions(self, public, status):
        if status == 1 and public == 'true':
            self._log.warning('Object already public')
            return
        elif status == 0 and public == 'false':
            self._log.warning('Object already private')
            return

        if public == 'true':
            self._log.info('Making object public')
            setter = '1'
        else:
            self._log.info('Making object private')
            setter = '0'

        r = self._api.get_object_public(setter=setter,
                                       object_id=self._obj.object_id)

        return r.get('result')

    def _folder_create(self, folder_name, folder_token=None):
        setter = None if folder_token else '0'
        data = {'name': folder_name}
        response = self._api.get_object_folder_create(data=data,
                                                     folder_id=folder_token,
                                                     setter=setter,
                                                     object_id=self._obj.object_id)

        self._log.debug(
            'Creating folder {0}, elapsed {1}, result: {2}'.format(folder_name,
                                                                   response.elapsed.total_seconds(),
                                                                   response.content))
        response = response.json()

        if response.get('result'):
            return response.get('upload_id')
        else:
            self._log.error(
                'Folder {0} wasn\'t created: {1}'.format(folder_name,
                                                         response))
            sys.exit(1)

    def _upload_file(self, file, upload_url):
        self.filename = self._path_leaf(file)
        payload = MultipartEncoder(
            fields={'file': (self.filename, open(file, 'rb').read())})
        monitor = MultipartEncoderMonitor(payload, self.__callback)

        r = self._api._session.post(upload_url, data=monitor, headers={
            'Content-Type': monitor.content_type})
        r.raise_for_status()

        return r

    def __callback(self, monitor):
        print('Uploading {0}: {1:.1f}%\r'.format(self.filename,
                                                 monitor.bytes_read / monitor.len * 100),
                                                 end='')
        if sys.platform != 'win32':
            sys.stdout.write("\033[K")

    def _scan_dir(self, dir_path):
        files = []
        dirs = []

        self._log.info('Current working dir {0}'.format(dir_path))

        with os.scandir(dir_path) as it:
            for entry in it:
                if entry.is_file():
                    files.append(entry.path)
                if entry.is_dir():
                    dirs.append(entry.path)

        return files, dirs

    @staticmethod
    def _path_leaf(path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    @staticmethod
    def _process_hashes(hashes, uploaded_sha1, uploaded_crc32):
        msgs = []
        if hashes.get('sha1_state'):
            msgs.append(['SHA1 hashes match'])
        else:
            msgs.extend([['SHA1 hashes differ'],
                         ['Local SHA1:', hashes.get('sha1_local')],
                         ['Server SHA1:', uploaded_sha1]])
        if hashes.get('crc32_state'):
            msgs.append(['CRC32 hashes match'])
        else:
            msgs.extend([['CRC32 hashes differ'],
                         ['Local CRC32:', hashes.get('crc32_local')],
                         ['Server CRC32:', uploaded_crc32]])

        return msgs

    @staticmethod
    def _parse_hashes(args):
        result = [
            'sha1_state',
            'sha1_local',
            'crc32_state',
            'crc32_local',
        ]
        return {key: arg for (arg, key) in zip(args, result)}
