#! /usr/local/bin/python3.6

"""
Module to get the fame rating of wikipedia people.

Will use the following proxies for fame of the person/page:
    Number of references
    Number of words in the page
    Citations across each month
"""

import ssl
import urllib.request
import json


def getjson(url):
    """Gets the json api data for a url page"""
    # get the api url
    api_head = 'https://en.wikipedia.org/w/api.php?format=json&action=parse&page='
    page_name = url.strip('https://en.wikipedia.org/wiki/')

    apiurl = api_head + page_name

    context = ssl._create_unverified_context()
    with urllib.request.urlopen(apiurl, context=context) as apiurl:
        data = json.loads(url.read().decode())

    print(data)


def references(url):
    """Gets the number of references at the end of an article"""
    return references


def words(url):
    """Gets the number of words in the article"""
    return len(words)


def citationspermth(url):
    """Gets a dataframe for the number of citations of a page per month
    Goes YYYY-MM, #citations"""
    return df


if __name__ == '__main__':
    getjson('https://en.wikipedia.org/wiki/Richard_Arkwright_junior')