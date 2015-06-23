
import logging
from models.validation import *

logger = logging.getLogger('codegen')


class GenError(Exception):
    '''
    A marker exception raised by the generator.
    '''
    pass

class JsonFormatter(logging.Formatter):
    '''
    Formatter for the generator class.
    '''

    mapper = {
        'stage': 'during %s',
        'importing': 'importing %s',
        'reading' : 'field %s',
        'view' : 'view %s',
        'plot' : 'plot %s'
    }

    def format(self, record):
        allmsg = []

        for attr in ('stage', 'importing', 'reading', 'view', 'plot'):
            if hasattr(record,attr):
                allmsg.append(self.mapper[attr] % getattr(record,attr))

        allmsg.append(record.getMessage())
        return ":".join(allmsg)

class GenFormatter(JsonFormatter):

    def format(self, record):
        lvl = record.levelname
        msg = super().format(record)
        return "%s: %s" % (lvl, msg)



class JsonHandler(logging.Handler):
    '''
    A handler that appends json objects to
    a given list.
    '''
    def __init__(self, records):
        super().__init__()
        self.records = records
        self.setLevel(logging.INFO)

    def emit(self, record):
        obj = {
                'level': record.levelname,
                'message': self.format(record)
        }
        self.records.append(obj)


class GenHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()  # create it on standard error
        self.setLevel(logging.INFO)


class GenProcess(Process):
    '''
    The validation process for the simulation generation.
    '''
    def __init__(self, level=logging.INFO):
        super().__init__(name='generator', logger=logger)
        self.suppress(Exception)

        # create the messages list
        self.messages = []
        logger.propagate=True

        # configure logging
        root = logging.getLogger()
        root.setLevel(level)
        for h in root.handlers:
            root.removeHandler(h)

        self.gen_handler = GenHandler()
        self.json_handler = JsonHandler(self.messages)

        root.addHandler(self.gen_handler)
        root.addHandler(self.json_handler)
        self.gen_handler.setLevel(level)

        self.gen_formatter = GenFormatter()
        self.json_formatter = JsonFormatter()
        self.gen_handler.setFormatter(self.gen_formatter)
        self.json_handler.setFormatter(self.json_formatter)

        # other
        logging.getLogger('urllib3').setLevel(logging.WARN)
