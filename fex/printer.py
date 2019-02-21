import logging

from tabulate import tabulate
from fex.constants import HOST
from fex.utils import convert_size


class Printer:
    def __init__(self, obj):
        self._log = logging.getLogger(self.__class__.__name__)
        self._obj = obj

    def _parse_object(self, object, view_response, view_password=None,
                      secret=None, hint=None):
        date = object.headers['date']
        upload_time = object.elapsed.total_seconds()
        object = object.json()
        size = convert_size(object['size'])
        post = view_response.get('post')
        msgs = [
            ['File name:', object['name']],
            ['File size:', size],
            ['SHA1 server:', object['sha1']],
            ['CRC32 server:', object['crc32']],
            ['Upload date:', date],
            ['Object name:', post.split('\n', 1)[0]],
            ['Object description:',
             ('', post.split('\n', 1)[-1])[len(post.split('\n')) >= 2]],
            ['Object ID:', self._obj.object_id],
            ['Object URL:', '{0}/#!{1}'.format(HOST, self._obj.object_id)],
            ['Folder ID:', self._obj.folder_id],
            ['Folder name:', self._obj.folder_name],
            ['Folder URL:',
             '{0}/#!{1}/{2}'.format(HOST, self._obj.object_id,
                                    self._obj.folder_id or '')],
            ['Direct download URL:',
             '{0}/load/{1}/{2}'.format(HOST, self._obj.object_id,
                                       object['upload_id'])],
            ['Public access:',
             '{0}'.format((False, True)[view_response['public']])],
            ['Upload time:', '{:.1f} seconds'.format(upload_time)],
        ]

        if view_password:
            msgs.append([['Object password:', view_password]])
        if secret:
            msgs.extend([['Object password:', secret],
                         ['Password hint:', hint]])
        return msgs

    def print_on_complete(self, object, view_password, headers=None, showindex=None):
        parsed_obj = self._parse_object(object, view_password)
        headers = headers or []
        print(tabulate(parsed_obj, headers=headers, showindex=showindex))

    def print_mesasge(self, msg, headers=None, showindex=None):
        headers = headers or []
        print(tabulate(msg, headers=headers, showindex=showindex))
