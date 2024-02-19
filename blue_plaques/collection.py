#! /usr/local/bin/python3.7

"""
Collect the data.
Plaque Scrape, bp_normaliser and linker all together.
Plaque scrape gives a dataframe of person, year, address, person_year, wiki columns saved in wiki_bp_data.csv
Normaliser takes wiki_bp_data.csv to make normalised_bp_data.csv with PAON, Street and Postcode columns

294 of 848 had a property in PP-complete.
"""

import os
import re
import ssl
import urllib.request

from blue_plaques import tools
from utils.web import get_soup as soups
import pandas as pd
import logging

resources_file = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s %(levelno)s ')
file_handler = logging.FileHandler(f'{(os.path.dirname(os.path.dirname(__file__)))}/collection.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)


resources_file = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))


class PlaqueScrape:
    """Class for scraping BP data from wikipedia
    Gives person, year, address, person_year, wiki columns.
    Uses cached wiki files.
    'https://en.wikipedia.org/wiki/List_of_blue_plaques',  # The non london plaques
    'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London',
    'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_Royal_Borough_of_Kensington_and_Chelsea',
    'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_London_Borough_of_Camden',
    'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_the_City_of_Westminster'
    """

    def __init__(self):
        self.savefile = '{}wiki_bp_data.csv'.format(resources_file)

    @staticmethod
    def string_clean(string, person):
        """Removes all crap in brackets and other clutter"""
        string = string.strip()
        string = string.replace('–', '-')
        regex = re.compile(r'\(\w+\)')
        result = re.findall(regex, string)
        for item in result:
            string = string.replace(item, ' ')

        stuff_to_remove = ['\n', '\xa0', '(', ')']
        for item in stuff_to_remove:
            string = string.replace(item, ' ')

        if person is True:
            # Remove yyyy-yyyy dates
            regex = re.compile(r'\d\d\d\d-\d\d\d\d')
            result = re.findall(regex, string)
            for item in result:
                string = string.replace(item, ' ')
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
                if len(columns) == 1:
                    address = None
                    year = None
                else:
                    address = columns[2].text
                    year = columns[3].text
                    year = PlaqueScrape.string_clean(year, False)
                person = PlaqueScrape.string_clean(person, True)
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
        # df['person_year'] = df.apply(PlaqueScrape.person_year, axis=1)

        df.to_csv(self.savefile)
        return df


class NormaliseDF:
    """
    The idea is to pull the PAON, SAON, Street and postcode from an address.
    Set up framework that will do one address then wrap it up in the whole thing.
    """
    def __init__(self, df, addresses_column_name):
        self.df = df
        self.address_column = addresses_column_name
        if addresses_column_name not in df.columns:
            raise TypeError('Incorrect Column Name')
        self.pp = tools.read_pp()

    @staticmethod
    def get_postcode(address):
        pc = re.findall(r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}', address)
        if len(pc) == 0:
            return ''
        else:
            return pc[0].strip()

    def get_paon(self, address):
        """

        :param address:
        :return:
        """
        postcode = self.get_postcode(address)
        address = address.upper().replace(postcode, ' ').strip()

        if re.match(r'[0-9]+ ?- ?[0-9]+', address):  # num - num
            a, b = re.match(r'[0-9]+ ?- ?[0-9]+', address)[0].split('-')
            return f'{a.strip()} - {b.strip()}'.strip()

        elif re.match(r'[0-9]+[A-Z]? ', address):  # num or num letter
            return re.match(r'[0-9]+[A-Z]? ', address)[0].strip()

        elif re.match(r'[A-Z ]+, [0-9]+ ?- ?[0-9]+', address):  # name, num/num-num
            a, b = re.search(r'[0-9]+ ?- ?[0-9]+', address)[0].split('-')
            return f'{re.match(r"[A-Z ]+,", address)[0]} {a.strip()} - {b.strip()}'

        elif re.match(r'[A-Z ]+, [0-9]+ ', address):  # name, num/num-num
            return f'{re.match(r"[A-Z ]+, [0-9]+ ", address)[0]}'.strip()

        else:
            paons = list(set(self.pp.loc[self.pp['PAON'] == self.get_postcode(address)]['Street'].tolist()))
            for paon in paons:
                if paon in address:
                    return paon
        return None

    def get_street(self, address):
        address = address.upper().replace(self.get_postcode(address), '')

        streets = list(set(self.pp.loc[self.pp['Postcode'] == self.get_postcode(address)]['Street'].tolist()))
        streets = [x for x in streets if str(x) != 'nan']
        if len(streets) == 1:
            return streets[0]

        for street in streets:
            if street.replace("'", ' ') in address.replace("'", ' '):
                return street
        street_names = ['TERRACE', 'COURT', 'SQUARE', 'GATE', 'PLACE', 'ROAD', 'LANE', 'WALK', 'CRESCENT', 'AVENUE']
        for s in street_names:
            if len(re.findall(r'[A-Z ]+ {}'.format(s), address)) > 0:
                return re.findall(r'[A-Z ]+ {}'.format(s), address)[0]
        return None

    def parse_address(self, address):
        """
        Gets the paon, street and postcode from an address
        :return:
        """
        postcode = self.get_postcode(address)
        street = self.get_street(address)
        paon = self.get_paon(address)

        return paon, street, postcode

    def add_paon_street_pc_to_df(self, addresses):
        bp = self.df
        numbers = []
        streets = []
        pcs = []
        postition_tracker = 0
        for address in addresses:
            if address is None:
                logger.info(f'{address} is None')
                continue
            n, s, p = self.parse_address(address)
            logger.debug(f'{n}, {s}, {p}')
            print(f'{address}, {n}, {s}, {p} {postition_tracker}/{len(addresses)}')
            postition_tracker += 1
            numbers.append(n)
            streets.append(s)
            pcs.append(p)
        bp['PAON'] = numbers
        bp['Street'] = streets
        bp['Postcode'] = pcs
        return bp

    def main(self):
        addresses = self.df[self.address_column].tolist()
        addresses = [x for x in addresses if x is not None]
        self.df = self.add_paon_street_pc_to_df(addresses)
        self.df.to_csv(f'{resources_file}/normalised_bp_data.csv')
        return self.df


if __name__ == '__main__':
    pd.set_option('display.max_columns', 100)
    print(NormaliseDF(tools.read_bp(), 'address').main())

