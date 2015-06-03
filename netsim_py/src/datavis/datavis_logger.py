import logging
from models.validation import Process


class DatavisFormatter(logging.Formatter):

    def format(self, record):
        if hasattr(record, 'view'):
            return "view: \"%s\" -- %s" % (record.view["name"], record.getMessage())
        elif hasattr(record, 'plot'):
            return "plot: \"%s\" -- %s" % (record.plot["title"], record.getMessage())
        elif hasattr(record, 'derived_table'):
            return "view: \"%s\" -- %s" % (record.derived_table.name, record.getMessage())
        elif hasattr(record, 'plot_model'):
            return "view: \"%s\" -- %s" % (record.plot_model.rel.name, record.getMessage())
        else:
            return super().format(record)


class DatavisHandler(logging.Handler):

    def __init__(self, records):
        super().__init__(logging.INFO)
        self.records = records
        self.setFormatter(DatavisFormatter())

    def emit(self, record):
        print(self.format(record))
        self.records.append(self.format(record))


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
        self.logger = logging.getLogger('datavis.proc')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        super().__init__(name=name, logger=self.logger)
        self.addScopeHandler(DatavisHandler(self.record_list))

    @staticmethod
    def new_factory(blist):
        def factory(*args, **kwargs):
            return DatavisProcess(blist, *args, **kwargs)

        return factory