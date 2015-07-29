# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import logging
import unittest
import mock

from testfixtures import LogCapture
from testfixtures import Comparison as C, compare
from twisted.python.failure import Failure

from scrapy.utils.log import (failure_to_exc_info, TopLevelFormatter,
                              LogCounterHandler, StreamLogger, _get_handler)
from scrapy.utils.test import get_crawler
from scrapy.settings import Settings


class FailureToExcInfoTest(unittest.TestCase):

    def test_failure(self):
        try:
            0/0
        except ZeroDivisionError:
            exc_info = sys.exc_info()
            failure = Failure()

        self.assertTupleEqual(exc_info, failure_to_exc_info(failure))

    def test_non_failure(self):
        self.assertIsNone(failure_to_exc_info('test'))


class TopLevelFormatterTest(unittest.TestCase):

    def setUp(self):
        self.handler = LogCapture()
        self.handler.addFilter(TopLevelFormatter(['test']))

    def test_top_level_logger(self):
        logger = logging.getLogger('test')
        with self.handler as l:
            logger.warning('test log msg')

        l.check(('test', 'WARNING', 'test log msg'))

    def test_children_logger(self):
        logger = logging.getLogger('test.test1')
        with self.handler as l:
            logger.warning('test log msg')

        l.check(('test', 'WARNING', 'test log msg'))

    def test_overlapping_name_logger(self):
        logger = logging.getLogger('test2')
        with self.handler as l:
            logger.warning('test log msg')

        l.check(('test2', 'WARNING', 'test log msg'))

    def test_different_name_logger(self):
        logger = logging.getLogger('different')
        with self.handler as l:
            logger.warning('test log msg')

        l.check(('different', 'WARNING', 'test log msg'))


class gethandlerTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger()
        self.orig_handlers = self.logger.handlers
        self.logger.handlers = []
        self.level = self.logger.level
        self.settings_dict_1 = {
            'LOG_ENABLED': 1,
            'LOG_LEVEL': 'INFO',
            'LOG_DISPLAY_TOP_LEVEL_ONLY': 1,
            'LOG_FILE': 0,
            'LOG_FORMAT': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            'LOG_DATEFORMAT': '%Y-%m-%d %H:%M:%S',
        }
        self.settings_dict_2 = {
            'LOG_ENABLED': 1,
            'LOG_LEVEL': 'INFO',
            'LOG_DISPLAY_TOP_LEVEL_ONLY': 0,
            'LOG_FILE': 0,
            'LOG_FORMAT': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            'LOG_DATEFORMAT': '%Y-%m-%d %H:%M:%S',
        }

    def tearDown(self):
        self.logger.handlers = self.orig_handlers
        self.logger.level = self.level

    # def test_get_handler(self):
    #     settings = Settings(self.settings_dict_1)
    #     handler =  _get_handler(settings)
    #     self.logger.addHandler(handler)
    #     compare([
    #         C('logging.StreamHandler',
    #           filter = C('logging.Filter',
    #                      name='TopLevelFormatter',
    #                      strict = False),
    #           strict=False)
    #         ], self.logger.handlers)


    @mock.patch('logging.StreamHandler')
    def test_get_handler(self, mockHandler):
        settings = Settings(self.settings_dict_1)
        _get_handler(settings)
        self.assertTrue(mockHandler.addFilter.called)
        #handler.addFilter = mock.MagicMock()
        #TopLevelFormatter = mock.MagicMock()
        #self.assertTrue(TopLevelFormatter.called)
        #TopLevelFormatter.assert_called_with(['Scrapy'])
        #mockStream.addFilter.assert_called_with(TopLevelFormatter(['scrapy']))
        settings = Settings(self.settings_dict_2)
        _get_handler(settings)
        self.assertFalse(mockaddFilter.called)



class LogCounterHandlerTest(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger('test')
        self.logger.setLevel(logging.NOTSET)
        self.logger.propagate = False
        self.crawler = get_crawler(settings_dict={'LOG_LEVEL': 'WARNING'})
        self.handler = LogCounterHandler(self.crawler)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.propagate = True
        self.logger.removeHandler(self.handler)

    def test_init(self):
        self.assertIsNone(self.crawler.stats.get_value('log_count/DEBUG'))
        self.assertIsNone(self.crawler.stats.get_value('log_count/INFO'))
        self.assertIsNone(self.crawler.stats.get_value('log_count/WARNING'))
        self.assertIsNone(self.crawler.stats.get_value('log_count/ERROR'))
        self.assertIsNone(self.crawler.stats.get_value('log_count/CRITICAL'))

    def test_accepted_level(self):
        self.logger.error('test log msg')
        self.assertEqual(self.crawler.stats.get_value('log_count/ERROR'), 1)

    def test_filtered_out_level(self):
        self.logger.debug('test log msg')
        self.assertIsNone(self.crawler.stats.get_value('log_count/INFO'))


class StreamLoggerTest(unittest.TestCase):

    def setUp(self):
        self.stdout = sys.stdout
        logger = logging.getLogger('test')
        logger.setLevel(logging.WARNING)
        sys.stdout = StreamLogger(logger, logging.ERROR)

    def tearDown(self):
        sys.stdout = self.stdout

    def test_redirect(self):
        with LogCapture() as l:
            print('test log msg')
        l.check(('test', 'ERROR', 'test log msg'))
