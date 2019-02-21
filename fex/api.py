import logging
import os
import sys
from http.cookiejar import LWPCookieJar

import requests

import fex.exceptions
from fex.constants import HOST, REQUEST_HEADERS, API_ENDPOINTS


class API:
    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)
        self._base_url = '{host}{endpoint}{object_id}/{folder_id}{setter}'

        self._session = requests.Session()
        self._session.headers.update(REQUEST_HEADERS)
        self._session.cookies = None
        self._cookie_file = None

    def initialize_cookies(self, username):
        self._log.debug('Initializing cookies')
        path = '{0}\\'.format(os.getenv('Temp')) if sys.platform == 'win32' \
                                                                   else '/tmp/'
        self._cookie_file = '{0}{1}_cookiejar'.format(path, username)
        self._session.cookies = LWPCookieJar(self._cookie_file)

    def process_cookies(self):
        if os.path.isfile(self._cookie_file) and os.stat(
                self._cookie_file).st_size > 0:
            self._session.cookies.load(ignore_discard=True)
            self._log.info('Cookies from {0} loaded'.format(self._cookie_file))

            if self.get_account():
                return True
            else:
                self._log.warning('Cookies invalid, probably expired')
                self.purge_cookies()
        return False

    def purge_cookies(self):
        self._log.info('Purging cookies')
        with open(self._cookie_file, 'w'):
            pass

    def save_cookies(self):
        self._session.cookies.save(ignore_discard=True)
        self._log.info('Cookies saved to {0}'.format(self._cookie_file))

    def _make_request(self, endpoint, return_json=True, **kwargs):
        url = self._base_url.format(
            host=HOST,
            endpoint=endpoint,
            object_id=kwargs.get('object_id', ''),
            folder_id=kwargs.get('folder_id', ''),
            setter=kwargs.get('setter', ''))

        self._log.debug('Current url: {0}'.format(url))

        try:
            response = self._session.post(url, data=kwargs.get('data'),
                                          headers=kwargs.get('headers'))
            response.raise_for_status()
            # self._log.debug(
            #     'Current response from server: {0}'.format(response.json()))
            response = response.json() if return_json else response
        except Exception as err:
            err_msg = 'Fex API Error.'
            self._log.exception(err_msg)
            raise fex.exceptions.APIError(err_msg)
        return response

    def get_account(self):
        return self._make_request(API_ENDPOINTS['account'])

    def get_archive(self):
        return self._make_request(API_ENDPOINTS['archive'])

    def get_home(self):
        res = self._make_request(API_ENDPOINTS['home'])
        return res.get('object_list', [])

    def get_object_access(self):
        return self._make_request(API_ENDPOINTS['object_access'])

    def get_object_create(self):
        res = self._make_request(API_ENDPOINTS['object_create'])
        object_id = res.get('token')
        upload_server = res.get('fs_upload')[0]
        return upload_server, object_id

    def get_object_folder_create(self, object_id, folder_name, **kwargs):
        self._log.debug(
            'Folder id passed to API: {0}'.format(kwargs.get('folder_id')))
        data = {'name': folder_name}
        res = self._make_request(API_ENDPOINTS['object_folder_create'],
                                 data=data,
                                 folder_id=kwargs.get('folder_id'),
                                 setter=kwargs.get('setter', ''),
                                 object_id=object_id)
        if not res.get('result'):
            self._log.error('Folder {0} wasn\'t created: {1}'.format(folder_name, res))
            # TODO
            raise fex.exceptions.APIError
        return res.get('upload_id')

    def get_object_folder_list(self, data):
        return self._make_request(API_ENDPOINTS['object_folder_list'], data=data)

    def get_object_folder_view(self, folder_id):
        return self._make_request(API_ENDPOINTS['object_folder_view'],
                                 folder_id=folder_id)

    def get_object_free(self):
        return self._make_request(API_ENDPOINTS['object_free'])

    def get_object_own(self, object_id):
        res = self._make_request(API_ENDPOINTS['object_own'],
                                 object_id=object_id)
        if not res.get('result'):
            raise fex.exceptions.OwnObjectError('Own failed for '
                                                'object {0}'.format(object_id))

    def get_object_public(self, object_id, **kwargs):
        return self._make_request(API_ENDPOINTS['object_public'],
                                 object_id=object_id,
                                 setter=kwargs.get('setter'))

    def get_object_set_delete_time(self):
        return self._make_request(API_ENDPOINTS['object_set_delete_time'])

    def get_object_set_view_pass(self, object_id, secret, hint=None):
        payload = {'pass': secret, 'pass_hint': hint}
        res = self._make_request(API_ENDPOINTS['object_set_view_pass'],
                                 object_id=object_id, data=payload)
        if not res.get('result'):
            raise fex.exceptions.UploaderError('Password wasn\'t set')

    def get_object_update(self):
        res = self._make_request(API_ENDPOINTS['object_update'])
        return res

    def get_upload_server(self, object_id, view_password=None):
        res = self.get_object_view(view_password=view_password,
                                   object_id=object_id)
        if res.get('can_edit'):
            upload_server = res.get('fs_upload')[0]
        else:
            raise fex.exceptions.ObjectUploadPermissionsError('You don\'t '
                                   'have permissions to upload to this Object')
        return upload_server, res

    def get_object_view(self, object_id, view_password=None):
        res = self._make_request(API_ENDPOINTS['object_view'],
                                 object_id=object_id,
                                 data={'pass': view_password})
        return res

    def login(self, username, password, force=False):
        if force:
            self._log.info('Force login')
            self.purge_cookies()

        if not self.process_cookies():
            self._log.debug('Trying to log in')
            credentials = {'login': username,
                           'password': password}
            response = self._get_signin(credentials)
            self._verify_login(response, username)
            self.save_cookies()

    def _verify_login(self, response, username):
        err_msg = ''
        if response.get('result') \
                and (response.get('login') == username
                     or response.get('user', 0).get(
                    'login') == username):
            self._log.info('Login successful')
        elif not response.get('result') and not response.get('captcha'):
            err_msg = 'Authentication error, verify credentials'
            self._log.error(err_msg)
            self._log.debug('Response data: {0}'.format(response.text))
            self._log.debug('Cookies: {0}'.format(response.cookies))
        elif response.get('captcha'):
            err_msg = 'Authentication error, captcha request'
            self._log.error(err_msg)
            self._log.debug('Response data: {0}'.format(response.text))
        elif not response.get('result') and len(response.keys()) == 1:
            err_msg = 'Are you uploading to non-existing Object ID?'
            self._log.error(err_msg)
            self._log.debug('Response data: {0}'.format(response.text))
        else:
            err_msg = 'Can\'t verify login due to an unknown error'
            self._log.error(err_msg)
            self._log.debug('Response data: {0}'.format(response.text))

        if err_msg:
            raise fex.exceptions.UserLoginError(err_msg)

    def _get_signin(self, credentials):
        return self._make_request(API_ENDPOINTS['signin'], data=credentials)

    def get_upload_list_copy(self):
        return self._make_request(API_ENDPOINTS['upload_list_copy'])

    def get_upload_list_delete(self):
        return self._make_request(API_ENDPOINTS['upload_list_delete'])

    def get_upload_list_move(self):
        return self._make_request(API_ENDPOINTS['upload_list_move'])
