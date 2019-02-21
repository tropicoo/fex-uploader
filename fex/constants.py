HOST = 'https://fex.net'
REQUEST_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/61.0.3163.79 Safari/537.36'),
    'Host': 'fex.net',
    'Upgrade-Insecure-Requests': '1',
    'Accept-Encoding': 'gzip, deflate, br',
}

# USER_LOGIN_ERRORS = {
#     'auth_err': {'msg': 'Authentication error, verify credentials'},
#     'captcha_request':  {'msg': 'Authentication error, captcha request'},
#     'non_exist_obj_id':  {'msg': 'Are you uploading to non-existing Object ID?'}
# }

API_ENDPOINTS = {
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
