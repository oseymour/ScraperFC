import sys
sys.path.append('..')
from ScraperFC import Oddsportal, shared_functions # import local scraperfc

import unittest
from unittest.mock import MagicMock, patch
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re

class TestOddsportal(unittest.TestCase):
    
    def setUp(self):
        self.driver_mock = MagicMock()
        self.driver_mock.page_source = ''
        self.driver_mock.find_element.return_value = MagicMock()
        self.driver_mock.execute_script.return_value = None

        self.instance = Oddsportal()
        self.instance.driver = self.driver_mock
        
    def tearDown(self):
        self.instance.close()
        
    @patch('bs4.BeautifulSoup')
    def test_get_match_links(self, soup_mock):
        year = 2022
        league = 'EPL'
        url = shared_functions.sources['Oddsportal'][league]['url'] + f'-{year-1}-{year}/results/'
        
        # Create a mock HTML response with links from different leagues
        mock_html = '''
            <html>
                <body>
                    <a class="flex-col" href="/football/england/premier-league-2021-2022/a-vs-b-1/">
                        A vs B
                    </a>
                    <a class="flex-col" href="/football/england/championship-2021-2022/c-vs-d-1/">
                        C vs D
                    </a>
                    <a class="flex-col" href="/football/spain/laliga-2021-2022/e-vs-f-1/">
                        E vs F
                    </a>
                </body>
            </html>
        '''
        self.driver_mock.page_source = mock_html
        
        links = self.instance.get_match_links(year, league)
        print('**** ' + str(len(links)) + ' ****')
            
        self.driver_mock.get.assert_called_once_with(url)
        self.driver_mock.find_element.assert_called_once_with(By.TAG_NAME, 'html')
        self.driver_mock.execute_script.assert_called_with('return window.pageYOffset;')
        # self.driver_mock.execute_script.assert_called_with('arguments[0].scrollIntoView()') #, MagicMock())
        # self.driver_mock.execute_script.assert_called_with('arguments[0].click()')# , MagicMock())
        
        self.assertEqual(links, ['https://oddsportal.com/football/england/premier-league-2021-2022/a-vs-b-1/'])

