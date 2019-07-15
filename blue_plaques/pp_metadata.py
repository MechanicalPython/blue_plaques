#! /usr/local/bin/python3.7

"""
Aims -- to get the metadata/stats for the pp file: mean house prices for an area
Sub aims
    1. Mean, median, skew, distribution, sd of house price for an outward code

"""

import os

import pandas as pd
from blue_plaques import tools

resources = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))
meta_data_file = '{}metadata.csv'.format(resources)


class CalculateMetaData:
    """
    Calculates the pp-complete meta data for each of the outward codes and postcodes.

    Data structure?
    pandas dataframe probably the best.
    Outward Code    Year    Median house price 'median'     Mean house price 'mean'    'number'     'skew'    'sd'
    """

    def __init__(self):
        print('Calculating Metadata')
        self.pp = tools.read_pp()

    def calculateMean(self):
        print('Calculating mean')
        return self.pp['Price'].mean().reset_index().set_index(['Outward_code', 'Year']).rename(columns={"Price": "mean"})

    def calculateMedian(self):
        print('Calculating median')
        return self.pp['Price'].median().reset_index().set_index(['Outward_code', 'Year']).rename(columns={"Price": "median"})

    def calculateCount(self):
        print('Calculating count')
        return self.pp.agg(['count'])['Price'].reset_index().set_index(['Outward_code', 'Year'])

    def calculateSkew(self):
        print('Calculating skew')
        return self.pp.skew().reset_index().set_index(['Outward_code', 'Year'])

    def calculateSD(self):
        print('Calculating sd')
        return self.pp.std().reset_index().set_index(['Outward_code', 'Year']).rename(columns={"Price": "sd"})

    def calculate_metadata(self):
        self.pp['Year'] = pd.to_datetime(self.pp['Date_sold'])
        self.pp['Year'] = self.pp['Year'].dt.year
        self.pp = self.pp.drop('Date_sold', 1)
        self.pp = self.pp.groupby(['Outward_code', 'Year'])

        df = pd.concat([
            self.calculateMean(),
            self.calculateMedian(),
            self.calculateCount(),
            self.calculateSD()
            # self.calculateSkew()
        ], axis=1)

        return df


def load_meta_data(from_scratch=False):
    if os.path.exists(meta_data_file) is True and from_scratch is False:
        return pd.read_csv(meta_data_file).set_index(['Outward_code', 'Year'])
    else:
        df = CalculateMetaData().calculate_metadata()
        df.to_csv(meta_data_file)
        return df.set_index(['Outward_code', 'Year'])


if __name__ == '__main__':
    load_meta_data()

