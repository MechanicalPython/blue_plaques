#! /usr/local/bin/python3.7

"""
The main correlation is fame against % price change (((after- before))/ before) * 100

Input a wikipedia page url and output the fame level: size of the file.

Will use the following proxies for fame of the person/page:
    Links to
    Links from
    Page size
    Page views per day. Can get back to July 1st 2015.

2015 - 2007 data on https://dumps.wikimedia.org/other/pagecounts-raw/
Pre 2007 is seemingly lost to the mists of time.

BritishNewspaperArchive is a website that has archived a bunch of british newpapers. They can be slowly scraped with
bs4 but there is no API avaliable :( The data avaliable is limited: meta data for a result but little else.


Create a single comprehensive data file for fame. It would only be for exact addresses.
Need person fame levels and the housing data and then marry them and do the calculations in excel. 
"""

import datetime
import os
import pandas as pd
import requests
import pickle

from scipy.stats.stats import pearsonr
import matplotlib.pyplot as plt


from multiprocessing.dummy import Pool
from blue_plaques import tools, t_tests
from utils.web import get_soup, jsonApi
from mwviews.api import PageviewsClient

resources_file = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))


class WikiPageData:
    """
    Gets wiki page data for a single wiki page or a list of them. Allows wiki url or article name

    https://en.wikipedia.org/w/api.php?action=query&titles={article name}&format=json&prop=revisions&rvstart={start date}&rvprop=size|timestamp

    Websites that will be used

    https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/{article name} - Good overall stats
    soup contains the data like start date, links to, links from,

    https://xtools.wmflabs.org/api/articleinfo/en.wikipedia.org/{article name}
    This has the start date but little else.

    Use this for views per day. But needs to find the article origin date to make it work
    It only includes data back to July 1, 2015. To get older data, you will need to use stats.grok.se (See below).
    https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start}/{end}
    E.g. https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Foo/daily/20050101/20171207
    project = en.wikipedia
    access = all-agents
    agent = article name
    granularity = daily
    start = YYYYmmdd
    end = YYYmmdd

    actual wiki api url:
    https://en.wikipedia.org/w/api.php?action=query&titles={artical title}&prop=revisions&rvprop=content&format=json&formatversion=2

    https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&ppprop=disambiguation&generator=random&grnnamespace=0&grnlimit=10

    """
    def __init__(self, wikiurl):
        print(wikiurl)
        self.article = self.checkUrl(wikiurl).replace('https://en.wikipedia.org/wiki/', '')
        self.today = datetime.datetime.now().strftime('%Y%m%d')
        self.xtools_soup = get_soup(f'https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/{self.article}')
        self.xtoolsapi_soup = jsonApi(f'https://xtools.wmflabs.org/api/articleinfo/en.wikipedia.org/{self.article}')

    @staticmethod
    def checkUrl(article):
        """Checks for redirected wiki-only urls and if it's a disambiguation page"""
        url = article.replace(' ', '_')
        if 'https://en.wikipedia.org/wiki/' not in url:
            # Assume it's just the article heading
            url = 'https://en.wikipedia.org/wiki/{}'.format(url)
            if requests.get(url).status_code is not 200:

                # Try and pull it from a google search
                try:
                    gsoup = get_soup('https://www.google.co.uk/search?q={}+wikipedia'.format(article.replace(' ', '+')))
                    results = gsoup.find('div', {'class': "srg"})
                    links = results.find_all('div', {'class': 'g'})
                    links = [link.find('a').get('href') for link in links]
                    for link in links:
                        if 'https://en.wikipedia.org/wiki/' in link:
                            return link
                except AttributeError as ae:
                    print('ERROR: Attribute error: {} for {}'.format(ae, article))

                raise UserWarning('Could not find a wiki url')
        soup = get_soup(url)
        if soup.find('table', id='disambigbox') is not None:
            raise UserWarning('Disambiguation page, not real page')
        redirect = soup.find('link', rel='canonical')['href']
        return redirect

    def getLinksTo(self):
        """Gets text after 'Links to this page' as int"""
        trs = self.xtools_soup.find_all('tr')
        for tr in trs:
            if 'Links to this page' in tr.text:
                return int(tr.find_all('td')[1].text.replace(',', ''))

    def getLinksFrom(self):
        """Gets text after 'Links from this page' as int"""
        trs = self.xtools_soup.find_all('tr')
        for tr in trs:
            if 'Links from this page' in tr.text:
                return int(tr.find_all('td')[1].text.replace(',', ''))

    def getPageSize(self):
        """Gets text after 'Page size' adn returns integer in bytes"""
        trs = self.xtools_soup.find_all('tr')
        for tr in trs:
            if 'Page size' in tr.text:
                bytes = tr.find_all('td')[1].text.replace('bytes', '').replace(',', '')
                integer = int(bytes.replace(',', ''))
                return integer

    def getPublishDate(self):
        """Returns YYYYmmdd date format specifically for use in wikiapi url"""
        return datetime.datetime.strptime(self.xtoolsapi_soup['created_at'], '%Y-%m-%d').strftime('%Y%m%d')

    def getViewsPerDay(self):  # pageviews own thing
        """Gets a time series dataframe: date (as index), views (column is article name)
        Will be using 'mwviews' package"""
        p = PageviewsClient('en')
        print(self.article)
        data = p.article_views('en.wikipedia',
                               [self.article],
                               granularity='daily',
                               start=self.getPublishDate(),
                               end=datetime.datetime.now().strftime('%Y%m%d'))
        df = pd.DataFrame.from_dict(data, orient='index').dropna()
        return df

    def getEditsPerMonth(self):
        """Gets the average number of wikipedia edits per day"""
        table = self.xtools_soup.find_all('section', {'id': 'month-counts'})[0].find_all('table')[0].find_all('tr')[1:]
        editsData = {}
        for row in table:
            month = row.find('td', {'class': 'sort-entry--month'}).text.strip()
            edits = row.find('td', {'class': 'sort-entry--edits'}).text.strip()
            minor_edits = row.find('td', {'class': 'sort-entry--minor-edits'}).text.strip()
            editsData.update({month: {'Edits': edits, 'Minor Edits': minor_edits}})

        return pd.DataFrame.from_dict(editsData, orient='index')

    def getAllData(self):
        return {self.article:
                   {'Links To': self.getLinksTo(),
                    'Links From': self.getLinksFrom(),
                    'Page Size': self.getPageSize(),
                    'Publish Date': self.getPublishDate(),
                    'Page Views Per Day': self.getViewsPerDay(),
                    'Edits Per Month': self.getEditsPerMonth()
                    }
                }


class BritishNewspaperArchive:
    """Tries to scrape data from https://www.britishnewspaperarchive.co.uk search
    If it's two people then it's a combined score of a search for both people"""
    def __init__(self, person):
        self.person = person

    def make_url(self):
        self.person = self.person.replace(' ', '%20')
        url = f"""https://www.britishnewspaperarchive.co.uk/Search/Results?BasicSearch="{self.person}"&ExactSearch=True"""
        return url

    def get_total_number_of_hits(self):
        print(f'Getting hits for {self.person}')
        person = self.person.split(' and ')
        try:
            number_of_hits = 0
            for person in person:
                soup = get_soup(self.make_url())
                soup = soup.find('div', {'class': 'list-group collapse in'})
                dates = soup.find_all('a', {'class': 'list-group-item'})
                for date in dates:
                    hits = date.find('span', {'class': 'badge'}).text
                    number_of_hits += int(hits.replace(',', ''))
            return number_of_hits

        except Exception as e:
            print(f'Error for {person} -- {e}')
            return None


class BatchProcessFame:
    wiki_file = f'{resources_file}wiki_fame_data.pkl'  # Keys: wiki url
    bna_file = f'{resources_file}BNA_fame_data.pkl'    # Keys: person

    def __init__(self, input_ls):
        if os.path.exists(BatchProcessFame.wiki_file):
            with open(BatchProcessFame.wiki_file, 'rb') as f:
                self.wiki = pickle.load(f)
        else:
            with open(BatchProcessFame.wiki_file, 'wb') as f:
                self.wiki = {}
                pickle.dump(self.wiki, f)

        if os.path.exists(BatchProcessFame.bna_file):
            with open(BatchProcessFame.bna_file, 'rb') as f:
                self.bna = pickle.load(f)

        else:
            with open(BatchProcessFame.bna_file, 'wb') as f:
                self.bna = {}
                pickle.dump(self.bna, f)

        self.input_ls = input_ls

    def wiki_pages(self):
        """Will remove duplicate urls and will return a dict of {url: {dataaaa}}"""
        # def wiki_page_data(url):
        #     return WikiPageData(url).getAllData()
        #
        # pool = Pool(os.cpu_count() - 1)
        #
        # wiki_data = pool.map(wiki_page_data, self.input_ls)
        # pool.close()
        # pool.join()
        #
        # for url, soup in zip(self.input_ls, wiki_data.keys()):
        #     self.wiki.update({url: soup})
        for url in self.input_ls:
            if url not in self.wiki:
                try:
                    self.wiki.update({url: WikiPageData(url).getAllData()})
                except Exception:
                    print(f'Error for {url}')

        with open(BatchProcessFame.wiki_file, 'wb'):
            pickle.dump(self.wiki, BatchProcessFame.wiki_file)
        return self.wiki

    def bna_pages(self):
        """Will remove duplicate urls and will return a dict of {person: hits}"""
        def bna_page_data(person):
            return BritishNewspaperArchive(person).get_total_number_of_hits()

        pool = Pool(os.cpu_count() - 1)

        ban_data = pool.map(bna_page_data, self.input_ls)
        pool.close()
        pool.join()

        for url, soup in zip(self.input_ls, ban_data.keys()):
            self.bna.update({url: soup})

        with open(BatchProcessFame.bna_file, 'wb'):
            pickle.dump(self.bna, BatchProcessFame.bna_file)
        return self.wiki


class FameEffect:
    """
    Data inputs are fame values and percentage change.
    Pull wiki data from wiki_fame
    Output: two lists of per change and fame value in a csv.
    """
    def __init__(self, fame_type, area_type):
        if fame_type == 'wiki':
            self.fame = wiki_fame(tools.read_bp()['wiki'].tolist())  # {person: page size}
        elif fame_type == 'BNA':
            self.fame = BritishNewspaperArchive().batch_process_from_bp()  # {person: hits}
        else:
            raise TypeError('Not correct fame type')

        self.pp_data = linker.ExactLinker().main()  # {BP address: {paon: {saon: {before: {time: weighted price}, {afte
        self.area_type = area_type

    def get_per_change(self):
        pass


def fame_price_change_correlation():
    """Got a person: fame and address: {nested dict, use t_tests.RepeatedMeasures().convert_linker_to_lists
    pp-complete data: [{address: {'before': before, 'after': after}}, ]
    fame data: {person: fame value}
    Make dict of {fame: % change}
    percentage change = (((after- before))/ before) * 100

    Outputs: tmp_fameperchange.csv - fame level, house price percentage change, person.
    """
    address_to_person = tools.read_bp().set_index('address')['person'].to_dict()  # {address: person, }
    person_fame = BritishNewspaperArchive().batch_process_from_bp()  # {person: hits}
    address_to_data = t_tests.RepeatedMeasures().convert_linker_to_lists()  # [{address: {'before': int, 'after': int}}]

    fame_ls, per_change_ls, person_ls = [], [], []
    for address_dict in address_to_data:
        address = list(address_dict.keys())[0]
        for value in address_dict.values():
            before = value['before']
            after = value['after']

        per_change = (((after- before)) / before) * 100
        fame = person_fame[address_to_person[address]]  # Get person from address, get hits from person.
        if per_change is None or fame is None:
            continue
        fame_ls.append(fame)
        per_change_ls.append(per_change)
        person_ls.append(address_to_person[address])

    print(pearsonr(fame_ls, per_change_ls))  # correlation, p-value
    df = pd.DataFrame({'fame': fame_ls, 'perchange': per_change_ls, 'person': person_ls})
    df.to_csv(f'{resources_file}tmp_fameperchange.csv')


if __name__ == '__main__':
    # todo - Finish FameEffects to calculate the proper details. Include all working in the output.
    wiki = tools.read_bp()['wiki'].tolist()
    BatchProcessFame(wiki).wiki_pages()

