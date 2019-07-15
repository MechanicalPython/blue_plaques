#! /usr/local/bin/python3.7

"""
Takes the two files (pp compressed and normalised_bp_data.csv)
Collect the data and form lists for the t-tests to deal with.

For each bp address
    Find the exact matches: pp.loc[(pp['Postcode'] == PC) & (pp['PAON'] == PAON)]
    Get the before and after prices
    Weight those prices (price / median house price for that outward code)
    Average or either side
    Two lists for t-test

Repeated measures t-test
​    Repeated measures is a test of the same house before and after a plaque is installed.

Independent samples t-test
​    Measures blue plaque properties against other properties in that postcode. Two samples from the same population.
​    The population is the area of the houses (e.g. N1) and the two conditions are plaque houses and all other houses.

Single sample t-test
​    Measures a sample against the population. Took all houses that had blue plaques on it, both before and after it
    obtained the plaque, and compared that to the population of London houses.


"""

import os
import pickle
import statistics
import logging

import numpy as np
import pandas as pd

from blue_plaques import pp_metadata
from blue_plaques import tools
from scipy import stats
from utils.util import timer

resources_file = '{}/Resources'.format(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s %(funcName)s %(levelno)s ')
file_handler = logging.FileHandler(f'{(os.path.dirname(os.path.dirname(__file__)))}/collection.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)


def isbefore(d1: int, d2: int):
    """
    2000 > 1999, after
    2000 < 2001 before
    :param d1:
    :param d2:
    :return: True = before, false = after, None = same
    """
    d1 = int(d1)
    d2 = int(d2)
    if d1 > d2:
        return False
    elif d1 < d2:
        return True
    else:
        return None


class RepeatedMeasures:
    """
    Gets the data from all the relevant postcodes.
    """

    def __init__(self):
        self.pp = tools.read_pp()
        self.bp = tools.read_bp().set_index('address')
        self.metadata = pp_metadata.load_meta_data()
        self.data_file_path = f'{resources_file}/repeated_measures_data.pkl'

    def save_address_data(self, data):
        with open(self.data_file_path, 'wb') as f:
            pickle.dump(data, f)

    def load_address_data(self):
        with open(self.data_file_path, 'rb') as f:
            return pickle.load(f)

    @timer
    def get_address_data(self):
        """Gets the price and date info for all BP addresses
        return: [
                {'Address': bp address,
                'Install year': install year
                'Outward code': outcode,
                'Price data': [{'Date': date,
                                'Price': price},
                                ]
                }
            ]
        """
        return_ls = []
        total = len(self.bp)
        counter = 0
        for address, values in self.bp[['Postcode', 'PAON']].to_dict(orient='index').items():
            postcode = values['Postcode']
            paon = values['PAON']
            if postcode is np.nan or paon is np.nan:
                continue
            price_date_df = self.pp.loc[(self.pp['Postcode'] == postcode) & (self.pp['PAON'] == paon)][
                ['Price', 'Date_sold']].to_dict('index')
            price_data = []
            for i in price_date_df.values():
                price = i['Price']
                date = i['Date_sold']
                price_data.append({'Date': date, 'Price': price})
            return_ls.append({'Address': address,
                              'Install year': self.bp.at[address, 'year'],
                              'Outward code': postcode.split(' ')[0],
                              'Price data': price_data})
            counter += 1
            if counter % 5 == 0:  # Prints progress every 5
                print(f'{counter}/{total}')

        return return_ls

    def get_lists_from_address_data(self, address_data, measurement_type):
        """
        [
                {'Address': bp address,
                'Outward code': outcode,
                'Install year': year
                'Price data': [{'Date': date,
                                'Price': price},
                                ]
                }
            ]
        :param address_data, measurement_type:
        :return: before ls, after ls
        """
        if measurement_type not in ['either_side', 'mean']:
            raise AssertionError('measurement_type must be either_side or mean')

        master_before = []
        master_after = []
        for address in address_data:
            outcode = address['Outward code']
            if type(address['Install year']) == np.ndarray:
                installyr = address['Install year'].tolist()
                installyr = [pd.to_datetime(x).year for x in installyr]
                installyr = min(installyr)
            else:
                installyr = pd.to_datetime(address['Install year']).year

            before = {}  # {date: price, }
            after = {}  # {date: price, }
            for item in address['Price data']:
                date = item['Date'].year
                price = item['Price']
                price = price / self.metadata.at[(outcode, date), 'median']
                if isbefore(date, installyr) is True:
                    before.update({date: price})
                elif isbefore(date, installyr) is False:
                    after.update({date: price})
                else:
                    pass

            logger.info(f'{address}, {installyr}, before:{len(before)}, after:{len(after)}')
            if len(before) < 1 or len(after) < 1:
                continue
            elif measurement_type == 'mean':
                master_before.append(statistics.mean(list(before.values())))
                master_after.append(statistics.mean(list(after.values())))
            elif measurement_type == 'either_side':
                # after - min, before - max
                master_after.append(after[min(after.keys())])
                master_before.append(before[max(before.keys())])

        return master_before, master_after

    @staticmethod
    def repeated_measures_t_test(before, after):
        """Takes two lists: before and after"""
        meana = round(float(np.mean(after)), 3)
        sda = round(statistics.stdev(list(after)), 3)

        meanb = round(float(np.mean(before)), 3)
        sdb = round(statistics.stdev(list(before)), 3)

        t, p = stats.ttest_rel(after, before, nan_policy='omit')
        t = round(t, 4)
        p = round(p, 3)
        df = float(len(after) - 1)
        return p, t, df, meana, sda, meanb, sdb

    def main(self, measurement_type, load_cache=True):
        if load_cache is True and os.path.exists(self.data_file_path) is True:
            address_data = self.load_address_data()
        else:
            address_data = self.get_address_data()
            self.save_address_data(address_data)
        before, after = self.get_lists_from_address_data(address_data, measurement_type)
        p, t, df, meana, sda, meanb, sdb = self.repeated_measures_t_test(before, after)
        print(f'For {measurement_type} \n'
              f'p-value: {p}, t-obt: {t}, df: {df}, '
              f'mean before (sd): {meanb} ({sdb}, '
              f'mean after (sd): {meana} ({sda})')


# todo - while it works, there are only 41 items so some are being missed....

if __name__ == '__main__':
    r = RepeatedMeasures()
    r.main('mean')
    r.main('either_side')
