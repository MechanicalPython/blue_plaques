#! /usr/local/bin/python3.7

"""
Module to scrape the wiki for the blue plaques data from:

'https://en.wikipedia.org/wiki/List_of_blue_plaques',  # The non london plaques
'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London',
'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_Royal_Borough_of_Kensington_and_Chelsea',
'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_London_Borough_of_Camden',
'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_City_of_Westminster'

Outputs to 'Resources/wiki_bp_data.csv'
It works so no need to touch it.

"""

import os
import re
import ssl
import urllib.request

import bs4
import pandas as pd

resources_file = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))


def soups(url):
    """Get bs4 soup from url"""
    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent':
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)'
                'AppleWebKit/537.36 (KHTML, like Gecko)'
                'Chrome/35.0.1916.47 Safari/537.36'}
    )
    context = ssl._create_unverified_context()
    web_page = urllib.request.urlopen(req, context=context)
    soup = bs4.BeautifulSoup(web_page, 'html.parser')
    return soup


class PlaqueScrape:
    """Class for scraping BP data from wikipedia"""

    def __init__(self):
        self.savefile = '{}wiki_bp_data.csv'.format(resources_file)

    @staticmethod
    def string_clean(string, person):
        """Removes all crap in brackets and other clutter"""
        string = string.replace('–', '-')
        regex = re.compile(r'\(\w+\)')
        result = re.findall(regex, string)
        for item in result:
            string = string.replace(item, '')

        stuff_to_remove = ['\n', '\xa0', '(', ')']
        for item in stuff_to_remove:
            string = string.replace(item, '')

        if person is True:
            # Remove yyyy-yyyy dates
            regex = re.compile(r'\d\d\d\d-\d\d\d\d')
            result = re.findall(regex, string)
            for item in result:
                string = string.replace(item, '')
        return string

    @staticmethod
    def table_scrape(table):
        """
        Function takes in wiki table and outputs list of dictionaries
        :param table: wiki table
        :return: [{person, wiki, address, year}, ]
        """
        data_list = []  # list of dictionaries [{person, wiki, address, year}, ]
        wiki_head = 'https://en.wikipedia.org'
        head = table.find_all('tr', {'class': 'vevent'})
        if head != []:
            # Then it's a sortable table
            rows = table.find_all('tr', {'class': 'vevent'})
            for row in rows:  # No need to skip as vevent missed the heading
                columns = row.find_all(['th', 'td'])
                person = columns[0].text  # The person's name is the first column
                try:
                    persons_wiki = wiki_head + columns[0].find('a').get('href')
                except:
                    persons_wiki = None

                address = columns[2].text  # Third column is the address
                year = columns[3].text  # 4th column is the year

                if columns[2].find_all('span', {'class': 'plainlinks nourlexpansion'}) != []:
                    coord = columns[2].find_all('span', {'class': 'plainlinks nourlexpansion'})
                    address = address.replace(coord[0].text, '')
                person = PlaqueScrape.string_clean(person, True)
                year = PlaqueScrape.string_clean(year, False)
                data_list.append({'person': person, 'wiki': persons_wiki, 'address': address, 'year': year})

        else:
            # It's a normal table
            # Headings should always be Person, Inscription, Location, Year, Photo, Sometimes other stuff.
            rows = table.find_all('tr')
            heading = rows[0]
            for row in rows[1:]:  # First row is the heading
                columns = row.find_all('td')
                person = columns[0].text
                try:
                    persons_wiki = wiki_head + columns[0].find('a').get('href')
                except AttributeError:
                    persons_wiki = None
                address = columns[2].text
                year = columns[3].text

                person = PlaqueScrape.string_clean(person, True)
                year = PlaqueScrape.string_clean(year, False)
                data_list.append({'person': person, 'wiki': persons_wiki, 'address': address, 'year': year})
        return data_list

    @staticmethod
    def plaque_scrape(wiki_url):
        """
        Takes wikipedia url and returns list of dicts
        :param wiki_url:
        :return:
        """
        wiki_head = 'https://en.wikipedia.org'
        soup = soups(wiki_url)

        data = []  # [{person, wiki, address, year}, ]
        # Find all tables in this main page
        tables = soup.find_all('table', {'class': 'wikitable'})
        # First column is always the person it's for.
        # Location is always 3rd column and year is always 4th
        for table in tables:
            data.extend(PlaqueScrape.table_scrape(table))

        # Done with this page. Now going onto the other pages.
        other_links = soup.find_all('div', {'class': 'hatnote navigation-not-searchable'})
        for link in other_links:
            url = wiki_head + (link.find('a').get('href'))
            soup = soups(url)
            tables = soup.find_all('table', {'class': 'wikitable'})
            for table in tables:
                data.extend(PlaqueScrape.table_scrape(table))

        return data

    @staticmethod
    def person_year(row):
        return '{}_{}'.format(row['person'], row['year'].year)

    def main(self):
        """Scrapes and saves the data from url to defined folder
        :param: list of urls to scrape
        :param: where to store the dataframe """
        urls = ['https://en.wikipedia.org/wiki/List_of_blue_plaques',  # The non london plaques
                'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London',
                'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_Royal_Borough_of_Kensington_and_Chelsea',
                'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_London_Borough_of_Camden',
                'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_City_of_Westminster'
                ]
        data = []  # [{person, ...}]
        for url in urls:
            data.extend(PlaqueScrape.plaque_scrape(url))
        df = pd.DataFrame(data)
        df['year'] = pd.to_datetime(df['year'], errors='coerce', format='%Y')
        df = df.drop_duplicates()
        df = df.dropna()
        df['address'] = df['address'].str.replace('\n', ', ')

        # Make a new column that is person_year that can allow for dealing with legit duplicates
        df['person_year'] = df.apply(PlaqueScrape.person_year, axis=1)

        df.to_csv(self.savefile)
        return df


def load_wiki_data(from_scratch=False):
    if from_scratch is False:
        return pd.read_csv('{}wiki_bp_data.csv'.format(resources_file))
    if from_scratch is True:
        PlaqueScrape.main()


if __name__ == '__main__':
    PlaqueScrape().main()
