import logging

from tabulate import tabulate
from fex.constants import HOST
from fex.utils import convert_size


class Printer:
    def __init__(self, obj):
        self._host = 'https://{0}'.format(HOST)
        self._log = logging.getLogger(self.__class__.__name__)
        self._obj = obj

    def _parse_object(self, **kwargs):
        uploaded = kwargs.get('uploaded')
        date = uploaded.headers['date']
        upload_time = uploaded.elapsed.total_seconds()
        uploaded = uploaded.json()
        size = convert_size(uploaded['size'])
        view_response = kwargs.get('view_response')
        post = view_response.get('post')

        msgs = []

        msgs.extend([
            ['File name:', uploaded['name']],
            ['File size:', size],
            ['SHA1 server:', uploaded['sha1']],
            ['CRC32 server:', uploaded['crc32']],
            ['Upload date:', date],
            ['Object name:', post.split('\n', 1)[0]],
            ['Object description:',
             ('', post.split('\n', 1)[-1])[len(post.split('\n')) >= 2]],
            ['Object ID:', self._obj.object_id],
            ['Object URL:', '{0}/#!{1}'.format(self._host, self._obj.object_id)],
            ['Folder ID:', self._obj.folder_id],
            ['Folder name:', self._obj.folder_name],
            ['Folder URL:',
             '{0}/#!{1}/{2}'.format(self._host, self._obj.object_id,
                                    self._obj.folder_id or '')],
            ['Direct download URL:',
             '{0}/load/{1}/{2}'.format(self._host, self._obj.object_id,
                                       uploaded['upload_id'])],
            ['Public access',
             '{0}'.format((False, True)[view_response['public']])],
            ['Upload time:', '{:.1f} seconds'.format(upload_time)],
        ])

        if kwargs.get('view_password'):
            msgs.append([['Object password:', kwargs.get('view_password')]])
        if kwargs.get('secret'):
            msgs.extend([['Object password:', kwargs.get('secret')],
                         ['Password hint:', kwargs.get('hint')]])

        return msgs

    def print_on_complete(self, data, headers=None, showindex=None):
        if headers is None:
            headers = []
        self._log.info(tabulate(data, headers=headers, showindex=showindex))
