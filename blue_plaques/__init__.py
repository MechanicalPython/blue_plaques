#! /usr/local/bin/python3.6

# dict format -
# {Unique ID:
# [
#     Price,
#     Date sold,
#     Postcode,
#     Property type,
#     New build,
#     Estate type,
#     PAON,
#     SAON,
#     Street/Road,
#     Locality,
#     Town/City,
#     District,
#     County,
#     PPD Category,
#     Record Status
#     ]
#     }
"""
__init__ file for blue plaques
This module is designed to take information from the wikipedia page containing all the data on blue plaques in London
and land registry data from the government website.
Three t-tests were conducted on the data gathered in an attempt to reduce the error in the analysis.

ALl price data was weighted in some capacity. Mostly it was as a proportion of the average house price for that year
and area (e.g. if N1 2NU the area is N1). This is to account for the general inflation of house prices over time.

All prices are assumed to be normally distributed and the population mean on 1.00070 shows that this assumption is well
founded, as that is expected from normally distributed data (the average weighted price of all houses should be 1 if
normally distributed)

Independent samples t-test
    Measures blue plaque properties against other properties in that postcode. Two samples from the same population.
    The population is the area of the houses (e.g. N1) and the two conditions are plaque houses and all other houses.
    May need to append code to ignore BP houses before plaque installation.
    #####

Repeated measures t-test
    Repeated measures is a test of the same house before and after a plaque is installed. Null hypothesis is that there
    will be no difference between house prices before and after blue plaque installation.


Single sample t-test
    Measures a sample against the population. Took all houses that had blue plaques on it, both before and after it
    obtained the plaque, and compared that to the population of london houses.
    ####
    Should really do single sample for houses sold before and houses sold after blue plaque installation. Need to
    do and change that.
    #####
"""

from blue_plaques.blue_plaques import plaque_scrape
from blue_plaques.blue_plaques import analysis_3
import requests
import os


def from_scratch(folder):
    """Gathers the soup from wiki source and csv from url (both hard coded in) and then runs analysis in the folder
    that is defined for the module
    :param: folder - what folder you wish to work in
    """
    # Check folder is correct
    if folder[-1:] != '/':
        folder = folder + '/'

    if os.path.exists(folder) is False:
        raise FileNotFoundError(
            'You did not enter a valid folder path. It should be something like: /Users/ME/Documents/folder/'
        )

    # Save the csv file from source
    # https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads

    csv_url = 'http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-complete.csv'
    r = requests.get(csv_url)
    with open(folder + 'pp-complete.csv', 'wb') as f:
        f.write(r.content)

    # Gather the soup and save data to bp_info.csv inside folder (defined above)
    plaque_scrape.main('https://en.wikipedia.org/wiki/List_of_English_Heritage_blue_plaques_in_London',
                       folder)

    bp_file = folder + 'bp_csv.csv'

    csv_file = folder + 'pp-complete.csv'
    # Run analysis on data

    files = analysis_3.Data(csv_file, bp_file)
    data = (analysis_3.main(files, shortcut=False))
    return data


def from_download(land_reg_file, bp_file):
    """If you have collected the bp csv file and land reg csv file from Github module page, use this by inputting
    their file paths"""
    if os.path.exists(land_reg_file) is False or os.path.exists(bp_file) is False:
        raise FileNotFoundError('One of the inputted file paths is not correct. Please input full file path')

    files = analysis_3.Data(land_reg_file, bp_file)
    data = (analysis_3.main(files, shortcut=False))
    return data


