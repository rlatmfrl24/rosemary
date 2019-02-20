import logging

mylogger = logging.getLogger('rm')
mylogger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
mylogger.addHandler(stream_handler)
mylogger.info('server')