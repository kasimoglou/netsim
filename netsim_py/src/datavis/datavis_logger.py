import logging
from models.validation import Process


class DatavisFormatter(logging.Formatter):

    def format(self, record):
        if hasattr(record, 'view'):
            assert isinstance(record.view, str)
            if hasattr(record, 'plot'):
                assert isinstance(record.plot, str)
                return "view: \"%s\" plot:\"%s\" -- %s" % (record.view, record.plot, record.getMessage())
            return "view: \"%s\" -- %s" % (record.view, record.getMessage())
        else:
            return super().format(record)


class DatavisHandler(logging.Handler):

    def __init__(self, records):
        super().__init__(logging.INFO)
        self.records = records
        self.setFormatter(DatavisFormatter())

    def emit(self, record):
        message = self.format(record)
        rec = {
            'level': record.levelname,
            'message': message
        }
        self.records.append(rec)


class DatavisProcess(Process):
    '''
    This class creates instances of binds the attribute to a fixed list.
    This is to ensure that all handlers created by instances
    append to the same list.

    Static method new_factory() returns a new factory function
    for this class, bound to a specified list.
    '''

    def __init__(self, record_list, name=None):
        self.record_list = record_list
        self.logger = logging.getLogger('datavis')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = True
        super().__init__(name=name, logger=self.logger)
        self.suppress(Exception)
        self.addScopeHandler(DatavisHandler(self.record_list))

    @staticmethod
    def new_factory(blist):
        def factory(*args, **kwargs):
            return DatavisProcess(blist, *args, **kwargs)
        return factory

