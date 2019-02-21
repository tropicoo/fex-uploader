# Fex Uploader
FEX.NET Uploader (Beta)


# Installation
```bash
git clone https://github.com/tropicoo/fex_uploader.git
pip3 install requests requests-toolbelt tabulate
```

# Usage
```
$ python fex_uploader.py -h

usage: fex_uploader.py [-h] [-a] [-u USERNAME] [-p PASSWORD] [-s SECRET]
                       [--hint HINT] [--folder_name FOLDER_NAME]
                       [-o OBJECT_ID] [-f FILE_LIST [FILE_LIST ...]]
                       [--view-password VIEW_PASSWORD]
                       [--object-name OBJECT_NAME]
                       [--object-description OBJECT_DESCRIPTION] [-d DIR_PATH]
                       [--force] [--own OWN_OBJECT_ID [OWN_OBJECT_ID ...]]
                       [--folder-create FOLDER_CREATE] [--folder FOLDER_ID]
                       [--list-dirs] [--public {true,false}] [--version]

FEX.net uploader

optional arguments:
  -h, --help            show this help message and exit
  -a, --anonymous       upload anonymously
  -s SECRET, --secret SECRET
                        set a password for an object
  --hint HINT           set a password hint for an object
  --folder_name FOLDER_NAME
                        folder name to be created
  --view-password VIEW_PASSWORD
                        object's password
  --object-name OBJECT_NAME
                        object's name
  --object-description OBJECT_DESCRIPTION
                        object's description
  -d DIR_PATH, --dir DIR_PATH
                        recursive upload of directory
  --force               force login
  --own OWN_OBJECT_ID [OWN_OBJECT_ID ...]
                        inherit object
  --folder-create FOLDER_CREATE
                        create folder with name
  --folder FOLDER_ID    upload to existent folder id, object id required
  --list-dirs           list folders for object
  --public {true,false}
                        make object public or private, default true
  --version             show program's version number and exit

user upload:
  -u USERNAME, --user USERNAME
                        set a username
  -p PASSWORD, --password PASSWORD
                        set a password
  -o OBJECT_ID, --object OBJECT_ID
                        set an object id
  -f FILE_LIST [FILE_LIST ...], --file FILE_LIST [FILE_LIST ...]
                        file name(s)
```
