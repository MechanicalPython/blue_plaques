#! /usr/local/bin/python3.6

"""Module to scrape the wiki for the blue plaques stuff
dict format - {Person: [persons wiki page, address, year issued], ...}"""

# import json
# import re
# import ssl
# import urllib.request
#
# import bs4
# import pandas as pd

# todo - add https://en.wikipedia.org/wiki/List_of_blue_plaques to plaques
# todo - add tests and docs and look


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
    # noinspection PyProtectedMember
    context = ssl._create_unverified_context()
    web_page = urllib.request.urlopen(req, context=context)
    soup = bs4.BeautifulSoup(web_page, 'html.parser')
    return soup


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


def table_scrape(table):
    """Function to parse a single table and output"""
    temp_dict = []
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
            person = string_clean(person, True)
            year = string_clean(year, False)
            temp_dict.append({'person': person, 'wiki': persons_wiki, 'address': address, 'year': year})

    else:
        # It's a normal table
        # Headings should always be Person, Inscription, Location, Year, Photo, Sometimes other stuff.
        rows = table.find_all('tr')
        heading = rows[0]
        for row in rows[1:]:  # First row is the heading
            columns = row.find_all('td')
            person = columns[0].text
            persons_wiki = wiki_head + columns[0].find('a').get('href')
            address = columns[2].text
            year = columns[3].text

            person = string_clean(person, True)
            year = string_clean(year, False)
            temp_dict.append({'person': person, 'wiki': persons_wiki, 'address': address, 'year': year})
    return temp_dict


def plaque_scrape(wiki_url):
    """The page has tables and links to other tables that can be used.
    args - the main wiki url: https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London
    returns - dict {Person: [persons wiki page, address, year issued], ...} saved to ./blue_plaques.txt"""
    wiki_head = 'https://en.wikipedia.org'
    soup = soups(wiki_url)

    plaque_dict = []
    # Find all tables in this main page
    tables = soup.find_all('table', {'class': 'wikitable'})
    # First column is always the person it's for.
    # Location is always 3rd column and year is always 4th
    for table in tables:
        plaque_dict.extend(table_scrape(table))

    # Done with this page. Now going onto the other pages.
    other_links = soup.find_all('div', {'class': 'hatnote navigation-not-searchable'})
    for link in other_links:
        url = wiki_head + (link.find('a').get('href'))
        soup = soups(url)
        tables = soup.find_all('table', {'class': 'wikitable'})
        for table in tables:
            plaque_dict.extend(table_scrape(table))

    return plaque_dict


def dict_to_df(dict_file, folder):
    """Converts the plaque scrape dict to a dataframe. """
    data = pd.read_json(dict_file)
    df = pd.DataFrame(data)
    df.columns = (['Address', 'Person', 'Wiki', 'Year'])

    df.to_csv(folder + 'bp_csv.csv', index=False)


def main(url, folder):
    """Scrapes and saves the data from url to defined folder
    url - 'https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London'
    folder - /Users/Matt/pyprojects/blue_plaques/"""

    dict = plaque_scrape(url)

    with open(folder + 'bp_info.txt', 'w') as infile:
        json.dump(dict, infile, sort_keys=True, indent=4)

    dict_to_df(folder + 'bp_info.txt', folder)
#
#
# if __name__ == '__main__':
#     # main('https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London',
#     #      '/Users/Matt/pyprojects/blue_plaques/')
#     pass