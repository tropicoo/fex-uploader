import logging


class Object:
    def __init__(self, args):
        self._log = logging.getLogger(self.__class__.__name__)
        self._create_attributes(args)

        # add as argparse argument
        self.folder_name = None

    def _create_attributes(self, args):
        for key in args:
            self._log.debug(
                'Created attribute from argparse: {0}={1}'.format(key,
                                                                  args[key]))
            setattr(self, key, args[key])
