#! /usr/local/bin/python3.6

"""
Tools methods that are needed

"""

import os

import numpy as np
import pandas as pd

# Main resources
resources = f'{os.path.dirname(os.path.dirname(__file__))}/Resources'
pp_file = f'{resources}/pp-complete.csv'
bp_file = f'{resources}/normalised_bp_data.csv'
compressed_pp_data_file = f'{resources}/compressed_pp_data.h5'


def read_pp(csv_file=f'{pp_file}', short_cut=True, *args, **kwargs):
    """
    Columns: ID, Price, Date_sold, Postcode, PAON, SAON, Street, Outward_code
    :param csv_file:
    :param short_cut: if True, read compressed file. If False, read raw and compress and save file
    :return: DF of the land reg data
    """
    if short_cut is True and os.path.exists(compressed_pp_data_file) is True:  # ~1.5 min
        return pd.read_hdf(compressed_pp_data_file, 'df', *args, **kwargs)

    print('Compressing pp-complete. ETA 5-10 minutes')

    names = ['ID', 'Price', 'Date_sold', 'Postcode', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
             'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
             'Record_Status']

    df = pd.read_csv(csv_file, header=None, low_memory=False, names=names)  # 3m:2s
    df = df.drop(['Property_type', 'New_build', 'Estate_Type', 'Locality',
                  'Town_City', 'District', 'County', 'PPD_Category', 'Record_Status', 'ID'], axis=1)

    df = df.dropna(subset=['Price', 'Date_sold', 'Postcode'])

    # Make Inward_code column here, then cat it. Basically pre-do the work on splitting the postcode
    df['Outward_code'], df['Inward_code'] = df['Postcode'].str.split(' ', 1).str  # 22.9 seconds - acceptable
    df = df.drop('Inward_code', axis=1)

    cat_col = ['Postcode', 'PAON', 'SAON', 'Street', 'Outward_code']

    for col in cat_col:
        df[col] = df[col].astype('category')

    df['Price'] = df['Price'].astype(np.int64)  # 204 ms

    def lookup(s):
        """
        This is an extremely fast approach to datetime parsing.
        For large data, the same dates are often repeated. Rather than
        re-parse these, we store all unique dates, parse them, and
        use a lookup to convert all dates.
        """
        dates = {date: pd.to_datetime(date) for date in s.unique()}
        return s.map(dates)

    df['Date_sold'] = lookup(df['Date_sold'])  # 7.25 sec
    df = df.sort_values(by='Postcode')  #
    df = df.set_index('ID')
    print('Compressed pp-complete. Saving to {}'.format(compressed_pp_data_file))

    if compressed_pp_data_file is not None:
        df.to_hdf(compressed_pp_data_file, 'df', format='table')
    del df      # Clear memory
    print('Done!')
    return pd.read_hdf(compressed_pp_data_file, 'df')


def read_bp(file=bp_file):
    df = pd.read_csv(file)
    df['address'] = df['address'].str.upper()
    return df


def pp_lookup():
    pp = read_pp().set_index('Postcode')
    while True:
        postcode = str(input('What postcode?: ').upper().strip())
        if postcode == 'STOP':
            break
        try:
            print(list(pp.at[postcode, 'PAON']))
            print(list(set(pp.at[postcode, 'Street'])))
        except KeyError:
            print('Not a valid postcode')


if __name__ == '__main__':
    pass

