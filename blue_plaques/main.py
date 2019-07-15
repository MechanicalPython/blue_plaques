#! /usr/local/bin/python3.7

"""
__init__ file for blue plaques

1. Plaque scrape -- Pulls the data from wikipedia and shoves it to a csv file called wiki_bp_data.csv

2. bp_address_normalising.main() to try and get the PAON, street and Postcode for addresses created by plaque scrape

3. Manually go through normalised_bp_data.csv to correct the pain, street and postcode data.
   1. Note, can use pp-lookup.py for help with this

4. linker.ExactLinker (or PostcodeLinker later) creates a dict of {address: [ls of indexes from normalised_bp_data.csv]} to be saved and used by linker.ExtractBPAddressesData which is used by t-tests

5. t-tests.py does the t-test on the data provided by linker

Files needed in Resources
- Essential
    pp-complete.csv
    compresses_pp_data.h5 -- only paon, street, postcode, outward_code, sale date and price
    wiki_bp_data.csv -- from plaque_scrape.py
    normalised_bp_data.csv -- maunally normalised data
    metadata.csv -- contains outward code house price data.

- 'Shortcut' files
    exact_link.pkl -- the source of truth for the links: {bp address: [ls of pp indexes for that address]}
    exact_bp_address_data.pkl -- {address: {paon: {saon: {date: price}}}} for all exact bp addresses
"""

import os
import pickle

from blue_plaques import fame, linker, t_tests, bp_address_normalising, plaque_scrape, pp_lookup, tools, pp_metadata

resources_file = '{}/Resources'.format(os.path.dirname(os.path.dirname(__file__)))


# todo -- check this method
def check_files_are_up_to_date():
    # linker files have been changed. call make_linked_dict to go from scratch. main() loads the file
    """Creates a pkl file that marks if each of the files are up to date and updates them if not
    If the modification date on either pp-complete or normalised_bp_data, re do everything"""

    check_file = f'{resources_file}/check.pkl'

    # Init the file
    if os.path.exists(check_file) is False:
        pp_mod = os.path.getmtime(f'{resources_file}/pp-complete.csv')
        bp_mod = os.path.getmtime(f'{resources_file}/normalised_bp_data.csv')
        with open(check_file, 'wb') as f:
            pickle.dump({'pp': pp_mod, 'bp': bp_mod}, f)

    # Get file for last mod for files
    else:
        with open(check_file, 'rb') as f:
            d = pickle.load(f)
            pp_mod = d['pp']
            bp_mod = d['bp']

    if pp_mod != os.path.getmtime(f'{resources_file}/pp-complete.csv') or bp_mod != os.path.getmtime(f'{resources_file}/normalised_bp_data.csv'):
        print('UPDATING ALL FILES')
        # re do everything
        tools.read_pp(short_cut=False)  # compresses_bp_data.h5
        pp_metadata.load_meta_data(from_scratch=True)  # metadata.csv
        linker.ExactLinker().main()  # exact_link.pkl
        linker.ExtractBPAddressesData().main()  # exact_bp_address_data.pkl


def repeated_measures_ttest(from_scratch, average_type, area):
    """
    Get all the bp addresses normalised
        Return {bp address: {paon: str, Street: str, Postcode: str}
    Get the raw data from pp complete
        Return {bp address: {sale date: price, ...}}
    Find before and after
        Return {before: [[int, int], [int, int], ..], after: ...} (nested prices for each saon)
    Perform t-test on that data
        Return t-test result
    :return:
    """

    if from_scratch:
        plaque_scrape.load_wiki_data(from_scratch)
        bp_address_normalising.main()
        print('Now manually go through normalised_bp_data.csv')
        tools.pp_lookup()
        linker.ExtractBPAddressesData()
        t_tests.RepeatedMeasures().main()

    if from_scratch is False:
        t_tests.RepeatedMeasures(average_type=average_type, area=area).main()


if __name__ == '__main__':
    print('Main')

