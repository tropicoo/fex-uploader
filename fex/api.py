import logging
import os
import sys
from http.cookiejar import LWPCookieJar
from fex.constants import HOST, REQUEST_HEADERS
import requests


class Api:
    def __init__(self, obj):
        self._log = logging.getLogger(self.__class__.__name__)
        self._base_url = 'https://{host}{method}{object_id}/{folder_id}{setter}'
        self._endpoints = {
            'account': '/j_account',
            'archive': '/j_archive/',
            'home': '/j_home/',
            'object_access': '/j_object_access/',
            'object_create': '/j_object_create',
            'object_folder_create': '/j_object_folder_create/',
            'object_folder_list': '/j_object_folder_list/',
            'object_folder_view': '/j_object_folder_view/',
            'object_free': '/j_object_free/',
            'object_own': '/j_object_own/',
            'object_public': '/j_object_public/',
            'object_set_delete_time': '/j_object_set_delete_time/',
            'object_set_view_pass': '/j_object_set_view_pass/',
            'object_update': '/j_object_update/',
            'object_view': '/j_object_view/',
            'signin': '/j_signin/',
            'upload_list_copy': '/j_upload_list_copy/',
            'upload_list_delete': '/j_upload_list_delete/',
            'upload_list_move': '/j_upload_list_move/',
        }
        self._session = requests.Session()
        self._session.headers.update(REQUEST_HEADERS)
        self._session.cookies = None
        self._cookie_file = None
        self._initialize_cookies(obj)

    def _initialize_cookies(self, obj):
        path = '{0}\\'.format(
            os.getenv('Temp')) if sys.platform == 'win32' else '/tmp/'
        username = obj.username if obj.username else ''

        self._cookie_file = '{0}{1}_cookiejar'.format(path, username)
        self._session.cookies = LWPCookieJar(self._cookie_file)

    def process_cookies(self):
        return_state = False

        if os.path.isfile(self._cookie_file) and os.stat(
                self._cookie_file).st_size > 0:
            self._session.cookies.load(ignore_discard=True)
            self._log.info('Cookies from {0} loaded'.format(self._cookie_file))

            if self._verify_cookies():
                return_state = True
            else:
                self._log.warning('Cookies invalid, probably expired')
                self.purge_cookies()

        return return_state

    def _verify_cookies(self):
        return True if self.get_account() else False

    def purge_cookies(self):
        self._log.info('Purging cookies')
        with open(self._cookie_file, 'w'):
            pass

    def save_cookies(self):
        self._session.cookies.save(ignore_discard=True)
        self._log.info('Cookies saved to {0}'.format(self._cookie_file))

    def _make_request(self, api_method, return_json=True, **kwargs):
        url = self._base_url.format(
            host=HOST,
            method=api_method,
            object_id=kwargs.get('object_id', ''),
            folder_id=kwargs.get('folder_id', ''),
            setter=kwargs.get('setter', ''),
        )

        self._log.debug('Current request: {0}'.format(kwargs))
        self._log.debug('Current url: {0}'.format(url))

        try:
            response = self._session.post(url, data=kwargs.get('data', None),
                                          headers=kwargs.get('headers', None))
            response.raise_for_status()

            self._log.debug(
                'Current response from server: {0}'.format(response.json()))

        except requests.exceptions.RequestException as err:
            # TBD
            pass
        return response.json() if return_json else response

    def get_account(self, *args, **kwargs):
        res = self._make_request(self._endpoints['account'])
        return res

    def get_archive(self, *args, **kwargs):
        res = self._make_request(self._endpoints['archive'])
        return res

    def get_home(self, *args, **kwargs):
        res = self._make_request(self._endpoints['home'])
        return res

    def get_object_access(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_access'])
        return res

    def get_object_create(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_create'])
        return res

    def get_object_folder_create(self, object_id, **kwargs):
        self._log.debug(
            'Folder id passed to API: {0}'.format(kwargs.get('folder_id')))
        res = self._make_request(self._endpoints['object_folder_create'],
                                 return_json=False,
                                 data=kwargs.get('data'),
                                 folder_id=kwargs.get('folder_id'),
                                 setter=kwargs.get('setter'),
                                 object_id=object_id)
        return res

    def get_object_folder_list(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_folder_list'],
                                 data=kwargs.get('data'))
        return res

    def get_object_folder_view(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_folder_view'],
                                 folder_id=kwargs.get('folder_id'))
        return res

    def get_object_free(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_free'])
        return res

    def get_object_own(self, object_id, **kwargs):
        res = self._make_request(self._endpoints['object_own'],
                                 object_id=object_id)
        return res

    def get_object_public(self, object_id, **kwargs):
        res = self._make_request(self._endpoints['object_public'],
                                 object_id=object_id,
                                 setter=kwargs.get('setter'))
        return res

    def get_object_set_delete_time(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_set_delete_time'])
        return res

    def get_object_set_view_pass(self, object_id, **kwargs):
        res = self._make_request(self._endpoints['object_set_view_pass'],
                                 object_id=object_id, data=kwargs.get('data'))
        return res

    def get_object_update(self, *args, **kwargs):
        res = self._make_request(self._endpoints['object_update'])
        return res

    def get_object_view(self, object_id, view_password=None):
        res = self._make_request(self._endpoints['object_view'],
                                 object_id=object_id,
                                 data={'pass': view_password})
        return res

    def get_signin(self, *args, **kwargs):
        res = self._make_request(self._endpoints['signin'],
                                 data=kwargs.get('data'))
        return res

    def get_upload_list_copy(self, *args, **kwargs):
        res = self._make_request(self._endpoints['upload_list_copy'])
        return res

    def get_upload_list_delete(self, *args, **kwargs):
        res = self._make_request(self._endpoints['upload_list_delete'])
        return res

    def get_upload_list_move(self, *args, **kwargs):
        res = self._make_request(self._endpoints['upload_list_move'])
        return res