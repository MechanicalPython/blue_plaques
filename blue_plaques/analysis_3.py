#! /usr/local/bin/python3.6

"""
Module to see if there is a significant change in house price when Blue Plaques are installed on a house around London.
This would provide evidence for a halo effect for blue plaques when purchasing a house

This is a new function type that is more streamlined and user end friendly
It needs only the csv file and can produce as many tests as it needs
CSV file to be found at https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads

The main method runs the three t-tests

"""

import datetime
import math
import os
import re
import statistics

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats, integrate
import seaborn as sns


__version__ = 3

dp = 2
resources_file = '{}/Resources/'.format(os.path.dirname(os.getcwd()))


def timer(func):
    def f(*args, **kwargs):
        start = datetime.datetime.now()
        rv = func(*args, **kwargs)
        end = datetime.datetime.now()
        print('Time taken', end - start)
        return rv

    return f


def distribution_plot(area, year):
    """
    Shows the distribution for an area and year
    :param area:
    :param year:
    :return:
    """
    h = raw_for_area_year(files, area, year, short_cut=True)
    sns.set(color_codes=True)
    sns.distplot(h)

    plt.show()


def save_df(df, name):
    """
    Saves the dataframe to Resources file to be used for repeated dataframe uses.
    :param: Average prices dataframe
    :return: None
    """
    file_path = '{}{}.pkl'.format(resources_file, name)
    file = open(file_path, 'w')
    file.close()
    df.to_pickle(file_path)


def get_year(date):
    """Only accepts string from dataframe with year at start and returns int
    Takes 16 ish seconds per chunk (of 10**6 rows)"""
    dt = datetime.datetime.strptime(str(date), '%Y-%m-%d %H:%M').year
    return dt


def find_area(postcode):
    """
    Don't change this because it won't change the dataframe splits that have been done so will probably break
    :param postcode: The postcode to be split
    :return: area
    """
    if pd.isnull(postcode) is True:
        return None
    else:
        return postcode.split(' ')[0]


def repeated_measures_catcher(chunk, person, matches, bp_year):
    """
    Designed to make sure there is the data available and I've not messed up
    Needs to see if there is a house sold before and after for each house

    :param chunk:
    :param person:
    :param matches:
    :param bp_year:
    :return: False for not sufficient data, True for there is enough data
    """
    # Checks the chunk for a bp person's matches
    before = []
    after = []
    same = []
    # Is there before and after information?
    for ID in matches:
        data = chunk.loc[chunk['ID'] == ID].set_index('ID')
        year_sold = pd.to_datetime(data.get_value(ID, 'Date_sold')).year
        if year_sold > bp_year:
            after.append(year_sold)
        elif year_sold < bp_year:
            before.append(year_sold)
        else:
            same.append(year_sold)
    if len(before) == 0 or len(after) == 0:
        return False
    else:
        return True


def population_variation(avg_prices_df):
    """
    Calcuates the population variance
    variance = (∑X^2 - ( (∑X)2 / N) ) / N

    pop var = sum(1 - (price/average london price for that year)) ^ 2 /sample size
    :param files: the csv and bp files
    :param avg_prices_df: ['median', 'mean', 'number', 'sd', 'skew', 'sum_of_x', 'sum_of_x_sqr']
    :return: pop var and pop mean
    """

    sumX2 = avg_prices_df['sum_of_x_srq'].sum()
    sumX = avg_prices_df['sum_of_x'].sum()
    n = avg_prices_df['number'].sum()

    pop_var = (sumX2 - (sumX * sumX / n)) / n
    pop_mean = sumX / n
    return pop_var, pop_mean


def raw_for_area_year(files, area, year, short_cut=True):
    """Gets the raw data for a certain area and year"""
    name = '{}_{}'.format(area, year)
    if short_cut is True:
        df = pd.read_pickle(resources_file + 'all_prices_df.pkl')
    else:
        df = Data.all_prices_df(files)

    df = df[df.index == name]
    df = df.dropna(1)
    ls = df.values.tolist()
    return ls


class Data:
    """Holds the misc methods that are needed to get the data ready for the analysis class"""
    __slots__ = ['csv_file', 'bp_file']

    def __init__(self, csv_file, bp_file):
        """
        Define the file for the csv file containing the land registary data
        and the bp file that is made by plaque_scrape.py
        :param csv_file:
        :param bp_file:
        """
        self.csv_file = csv_file
        self.bp_file = bp_file

    def read_csv(self, chunk_power):
        """Reads the csv file in chunks
        :param self
        :param chunk_power - 6 is recommended for best performance
        :yield data frame"""
        chunksize = 10 ** chunk_power
        for chunk in pd.read_csv(self.csv_file, chunksize=chunksize):
            print('Chunk')
            df = pd.DataFrame(chunk)
            df.columns = ['ID', 'Price', 'Date_sold', 'Postcode', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
                          'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
                          'Record_Status']
            # Maybe put a check here? Make sure it's a legit file.
            # Drop nan rows for price, postcode or date_sold
            df = df.dropna(axis=0, subset=['Price', 'Date_sold', 'Postcode'], how='any')
            # df = (df[df['County'] == 'GREATER LONDON'])     # Removes ones not in Greater London
            yield df

    def read_bp(self):
        """Reads the bp data and makes it into a dataframe
        Changes it by iterating over the read file and making a new data frame
        Drops rows that don't have a year for the plaque installation.
        :param: self and the read bp is: Index, address, person, wiki, year
        :return : DataFrame. Columns = ['Person', 'Wiki', 'Year', 'House number', 'Address list', 'Postcode']"""
        df = pd.read_csv(self.bp_file)

        new_df = pd.DataFrame(columns=['Person', 'Wiki', 'Year', 'Number', 'Address_list', 'Postcode'])
        for row in df.itertuples():
            if pd.isnull(row.Person) is False:
                person = str(row.Person)
            else:
                person = np.nan
            wiki = str(row.Wiki)
            try:
                year = str(pd.to_datetime(str(int(float(row.Year)))).year)
            except ValueError:
                year = np.nan

            number = str(re.findall(r'\d+', row.Address)[0])
            try:
                postcode = str((re.findall(r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}', row.Address))[0])
            except IndexError as lsere:
                if str(lsere) == 'list index out of range':
                    postcode = 'nan'

            address_list = list(
                row.Address.replace(postcode, ' ').replace(number, ' ').replace(',', '').strip().split('\n'))
            tmp_df = pd.DataFrame([[person, wiki, year, number, address_list, postcode]],
                                  columns=['Person', 'Wiki', 'Year', 'Number', 'Address_list', 'Postcode']
                                  )
            new_df = new_df.append(tmp_df, ignore_index=True)

        return new_df

    def exact_bp_matches(self, chunk):
        """
        Finds and returns the BP matches from a csv chunk. This is then used to look up the data
        :param chunk:
        :return matches: dictionary - {Person: [ID, ID, ID], ..}
        """
        # Needs to find rows that match on PAON, postcode and Street/locality/Town_City
        # Group by postcode on both dataframes and see if there are any matches?
        bp = Data.read_bp(self)
        postcode_matches = pd.merge(bp, chunk, on=['Postcode'], how='inner')
        # Make both PAON and Number to same format so they can be matched.
        postcode_matches[['PAON', 'Number']] = postcode_matches[['PAON', 'Number']].apply(pd.to_numeric,
                                                                                          errors='coerce')

        # df is now all postcode matches
        # See for common PAON/Number columns
        df = postcode_matches[postcode_matches.PAON == postcode_matches.Number]
        # If any of Street, Locality, Town_City, District or County is in the Address_list, it's a full match
        indexes = []
        for row in df.itertuples():
            address_list = [item.lower() for item in row.Address_list]

            land_reg_list = [row.Street, row.Locality, row.Town_City]
            new_land_reg_list = []
            for item in land_reg_list:
                try:
                    new_land_reg_list.append(item.lower())
                except AttributeError as error:
                    pass
            if not any(x in new_land_reg_list for x in address_list):
                indexes.append(row.Index)

        df = df.drop(indexes)
        df = df.dropna(subset=['Postcode', 'Street'])
        matches = df.drop(['Address_list', 'Wiki', 'Number', 'Postcode', 'Property_type', 'Estate_Type', 'PAON', 'SAON',
                           'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category', 'Record_Status',
                           'New_build', 'Price', 'Date_sold', 'Year'], axis=1)
        matches_dict = {}
        for row in matches.itertuples():
            if row.Person in matches_dict.keys():
                matches_dict[row.Person].append(row.ID)
            else:
                matches_dict.update({row.Person: [row.ID]})

        return matches_dict

    def all_prices_df(self):
        """Gets the price data of all area by year
        """
        median_dict = {}
        for chunk in Data.read_csv(self, 6):
            df = chunk.drop(['ID', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
                             'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
                             'Record_Status'], 1)
            areas = chunk['Postcode'].apply(find_area)
            df['Postcode'] = areas

            df['Date_sold'] = df['Date_sold'].apply(get_year)

            df = df.groupby(['Postcode', 'Date_sold'])

            for group, df in df:
                n = '{}_{}'.format(str(group[0]), str(group[1]))
                try:
                    median_dict[n].extend(list(df['Price']))
                except KeyError:
                    median_dict[n] = list(df['Price'])

        df = pd.DataFrame.from_dict(median_dict, orient='index')
        return df

    @timer
    def house_prices_stats(self, short_cut=True):
        """
        Gets a df that has stats for all the area/year prices. Will have the median, mean, number, sd,
        normal distribution.
        :param short_cut: True for using the saved dataframe
        :return meadian: dataframe of stats per year/area
        """
        if short_cut is True:
            avg_prices = pd.read_pickle(resources_file + 'house_prices_stats.pkl')
            return avg_prices

        else:
            df = Data.all_prices_df(self)

            median = df.median(1)
            mean = df.mean(1)
            n = df.count(1)
            sd = df.std(1)
            skew = df.skew(1)
            sumx = df.sum(1)
            sumx2 = df.applymap(lambda x: x*x).sum(1)

            stats = pd.concat([median, mean, n, sd, skew, sumx, sumx2], axis=1)
            stats.columns = ['median', 'mean', 'number', 'sd', 'skew', 'sum_of_x', 'sum_of_x_sqr']
            stats = stats.reset_index()
            stats['Area'], stats['Year'] = stats['index'].str.split('_', 1).str
            stats = stats.drop(['index'], axis=1)

            return stats

    """
    Single methods that takes the csv file as the argument
    """
    # Repeated is dict of before and after installation average prices of a BP house
    repeated_measures_data = {}
    # Single sample is one list: sample prices. Pop var and mean are calculated sepetately
    single_sample_data = []
    # Independent samples is two lists: BP house prices and NBP prices that are in a BP postcode
    independent_samples_data = ([], [])

    def repeated_measures_save(self, chunk, avg_prices, avg_type):
        """
        Saves the data needed for a repreated measures t-test.
        Data needed is - Before and after house prices (weighted and averaged) for each BP house
        {'Person name: {'Before': [ls before prices], 'After': [ls after prices]}}
        Method is
            Check if row is a bp or not.
            Check the year of the sale
            Add weighted price to correct list
        :param: chunk
        :param: bp dtaframe
        :param: avg prices dataframe
        :param: string of type of average you want to use: mean or median
        :return: {'Person name: {'Before': [ls before prices], 'After': [ls after prices]}}
        """
        if avg_type != 'mean' and avg_type != 'median':
            raise KeyError('{} not allowed. Try mean or median'.format(avg_type))

        all_matches = Data.exact_bp_matches(self, chunk)  # In dictionary form - {person: [ls of IDs]}
        bps = Data.read_bp(self)
        final = {}
        for key, matches in all_matches.items():
            final.update({key: {'Before': [], 'After': []}})
            # If person not in dict, add them
            # Find the year of plaque, year of each house sold and their price
            row = (bps.loc[bps['Person'] == key])
            index = row.index[0]
            try:
                bp_year = int(row.get_value(index, 'Year'))
            except ValueError as e:
                continue

            area = find_area(row.get_value(index, 'Postcode'))
            for ID in matches:
                data = chunk.loc[chunk['ID'] == ID].set_index('ID')
                year_sold = pd.to_datetime(data.get_value(ID, 'Date_sold')).year
                price = int(data.get_value(ID, 'Price'))

                if year_sold < bp_year:  # Sold after bp installed
                    avg = (price / avg_prices[(avg_prices['Area'] == area) & (avg_prices['Year'] == year_sold)].iloc[0][
                        str(avg_type)])

                    final[key]['Before'].append(avg)
                elif year_sold > bp_year:  # Sold before bp installed
                    avg = (price / avg_prices[(avg_prices['Area'] == area) & (avg_prices['Year'] == year_sold)].iloc[0][
                        str(avg_type)])

                    final[key]['After'].append(avg)
                else:
                    pass

        return final

    def single_sample_save(self, chunk, avg_prices, avg_type):
        """
        Get all the london prices and all bp matches houses. Prices weighted by area
        pop var and pop mean have to be calculated separately and put into the equation.
        Skips houses where the blue plaque had yet to be installed
        :return: sample ls
        """
        if avg_type != 'mean' and avg_type != 'median':
            raise KeyError('{} not allowed. Try mean or median'.format(avg_type))
        bps = Data.exact_bp_matches(self, chunk)
        bp_data = Data.read_bp(self)
        # Just want to find the matches and add the weighted prices
        sample = []
        for key, matches in bps.items():
            for ID in matches:
                row = chunk.loc[chunk['ID'] == ID].set_index('ID')
                price = row.get_value(ID, 'Price')
                year = pd.to_datetime(row.get_value(ID, 'Date_sold')).year  # Year house sold
                area = find_area(row.get_value(ID, 'Postcode'))
                bp_year = bp_data[(bp_data['Person'] == key)].iloc[0]['Year']
                if int(bp_year) < int(year):  # Plaque installed before house sold    2015 < 2017 , 2015 > 2014
                    weighted_price = price / \
                                     avg_prices[(avg_prices['Area'] == area) & (avg_prices['Year'] == year)].iloc[0][
                                         str(avg_type)]
                    sample.append(weighted_price)
                else:
                    continue
        return sample

    def independent_samples_save(self, chunk, avg_prices, avg_type):
        """Two lists: exact bp prices and prices of houses within bp postcodes.
        Therefore, got to find all bp houses and then all houses that are in bp postcodes
        Skips houses where the blue plaque had yet to be installed
        """
        if avg_type != 'mean' and avg_type != 'median':
            raise KeyError('{} not allowed. Try mean or median'.format(avg_type))
        bpmatches = Data.exact_bp_matches(self, chunk)
        bp = Data.read_bp(self)
        areas = []
        data_set = ([], [])  # BP houses, other houses
        # Get a list of areas to be looked at, make it a dataframe, then reduce the chunk to what I want, then iterate
        for row in bp.itertuples():
            area = find_area(row.Postcode)
            areas.append(area)

        for row in chunk.itertuples():
            area = find_area(row.Postcode)
            if area is None:
                continue
            else:
                if area in areas and pd.isnull(row.Date_sold) is False and pd.isnull(row.Price) is False:

                    price = float(
                        format(row.Price /
                               avg_prices[(avg_prices['Area'] == area) &
                                          (avg_prices['Year'] == pd.to_datetime(row.Date_sold).year)].
                               iloc[0][str(avg_type)],
                               '.4g')
                    )

                    if row.ID in list(bpmatches.values())[0]:
                        # Add to right list
                        # Check year is after bp installation
                        for keyperson, ids in bpmatches.items():
                            if row.ID in ids:
                                person = keyperson
                                bp_year = bp[(bp['Person'] == person)].iloc[0]['Year']
                                house_year = pd.to_datetime(row.Date_sold).year
                                if int(bp_year) < int(house_year):  # 2015 < 2017 , 2015 > 2014
                                    data_set[0].append(price)

                    else:
                        # Add to left list
                        data_set[1].append(price)  # Year checking not needed as it's not a bp house.
        return data_set

    def getRepeatesMeasuresTable(self, short_cut):
        """
        Uses repestes_measures_save to get all the data for the table

        :return dataframe of data: ['Person', 'Postcode', 'Number', 'Year of BP installation', 'Weighted prices before',
         'Weighted prices after', 'SD']
        """
        avg_prices = Data.mean_prices(self, short_cut)
        bp = Data.read_bp(self)
        table = pd.DataFrame(
            columns=['Person', 'Postcode', 'Number', 'Year of BP installation', 'Weighted_prices_before',
                     'Weighted_prices_after'])
        overall_matches = {}
        for chunk in Data.read_csv(self, 6):
            # Stuff for repeated measures t-test - basically properly updating the data
            for person, bf_af in Data.repeated_measures_save(self, chunk, avg_prices).items():
                # Just using update caused the keys to be replaced which is not good.
                if person in overall_matches.keys():
                    # Add the new data
                    overall_matches[person]['Before'].extend(bf_af['Before'])
                    overall_matches[person]['After'].extend(bf_af['After'])
                else:
                    overall_matches.update({person: bf_af})

        # {Person name: {'Before': [ls before prices], 'After': [ls after prices]}}
        for person, data in overall_matches.items():
            before = data['Before']
            after = data['After']
            print(len(before), len(after))
            if len(before) == 0 or len(after) == 0:
                continue
            else:
                # ['Person', 'Wiki', 'Year', 'House number', 'Address list', 'Postcode']
                postcode = (bp[bp['Person'] == person]).iloc[0]['Postcode']
                number = (bp[bp['Person'] == person]).iloc[0]['Number']
                year = (bp[bp['Person'] == person]).iloc[0]['Year']
                before = data['Before']
                after = data['After']
                # Area', 'Year', 'Price_count_sum', 'Price_sum', 'SD', 'SumXSqr', 'Average_price']
                table = table.append(pd.DataFrame([[person, postcode, number, year, before, after]],
                                                  columns=['Person', 'Postcode', 'Number', 'Year of BP installation',
                                                           'Weighted_prices_before', 'Weighted_prices_after']))

        pd.DataFrame.to_csv(table, resources_file + 'repeated_meaures.csv')
        return table

    def getAveragePricesTable(self, shortcut=True, printer=True):
        """
        Spreadsheet with each repeated measures postcode, the area, the number of properties in that area for each year,
        the average price and SD for each area per year.

        :param printer: True = put df in csv, False is don't
        :param shortcut:    Use avg_price shortcut
        :return: df['Repeated measure postcode', 'area of house', 'year', '# of properties in that area', 'Avg price', '

        """
        # Get list of repeated measures postcodes
        bp = Data.read_bp(self)
        # todo - get the list of postcodes I want and then keep only those ones
        split = bp['Postcode'].str.split(' ', 1, expand=True).rename(columns={0: 'Area', 1: 'Postcode'})
        bp = pd.merge(split, bp, on='Postcode', how='right')

        areas = (split['Area']).drop_duplicates()
        areas = np.array(areas.dropna())

        # Drop non matches from avg_prices

        avg = Data.mean_prices(self, shortcut)

        avg = avg[avg['Area'].isin(areas)]

        # convert to excelc
        if printer is True:
            pd.DataFrame.to_csv(avg, resources_file + 'table.csv')

        return avg


class TTests:
    """Holds the t-test methods"""

    # noinspection PyStatementEffect
    @staticmethod
    def repeated_measures(before_after):
        """
        Repeated masures is a test of before and after a plaque is sold
        Therefore need - sample size, before mean, after mean and finally difference between before and after
        :param: {'Person name: {'Before': [ls before prices], 'After': [ls after prices]}}
        :return:t_obt and descriptive stats
        """
        # The plaque is raw so needs to reject unsuitable data points: ones with only a before/after data point
        # Data needed:
        avg_bf_ls = []  # ls of avg before scores
        avg_af_ls = []  # ls of avg after scores
        diff_ls = []  # ls of difference in avg before after scores
        diff_sqr_ls = []  # ls of diff scores squares
        sample_size = 0  # sample size
        for person, bfr_aft in before_after.items():
            # bfr_aft = {'Before': [ls], 'After': [ls]}
            try:
                bfr_aft['Before']
                bfr_aft['After']
            except TypeError:
                print('Type error, incorrect format for {} and {}'.format(person, bfr_aft))
                continue
            before_ls = bfr_aft['Before']
            after_ls = bfr_aft['After']
            if len(before_ls) != 0 and len(after_ls) != 0:
                sample_size += 1
                bf_avg = statistics.mean(before_ls)
                af_avg = statistics.mean(after_ls)
                avg_bf_ls.append(bf_avg)
                avg_af_ls.append(af_avg)
                diff_ls.append(bf_avg - af_avg)
                diff_sqr_ls.append((bf_avg - af_avg) ** 2)

        if sample_size < 2:
            return 'Error - sample size too small, only one participant'
        before_mean = (statistics.mean(avg_bf_ls))
        before_sd = statistics.stdev(avg_bf_ls)
        after_mean = (statistics.mean(avg_af_ls))
        after_sd = statistics.stdev(avg_af_ls)
        sum_d_2 = (sum(diff_sqr_ls))  # ∑d^2
        sum_d__2 = (sum(diff_ls) ** 2)  # (∑d)^2
        t_obt = ((before_mean - after_mean)
                 /
                 math.sqrt(
                     float(sum_d_2 - (sum_d__2 / sample_size))
                     /
                     float(sample_size * (sample_size - 1))
                 )
                 )

        df = sample_size - 1

        print("""
                Repeated measures t-test results - all values rounded to 2 d.p.:
                T-obtained = {}
                Degrees of Freedom = {}
                Before plaque installation mean and standard deviation = {} ({})
                After plaque installation mean and standard deviation = {} ({})
                """.format(round(t_obt, dp), df, round(before_mean, dp), round(before_sd, dp),
                           round(after_mean, dp), round(after_sd, dp)))

        return round(t_obt, dp), df, round(before_mean, dp), round(after_mean, dp)

    @staticmethod
    def single_sample(sample, pop_var=0.0, pop_mean=0.0):
        """
        Measures a sample against the population. The population here are the areas in which BPs exist.
        :param sample: ls of sample instances
        :param pop_var: given as raw value
        :param pop_mean: given as raw value
        :return: t_obt, df, sample_mean, pop_mean
        """
        sample_mean = statistics.mean(sample)
        s1 = statistics.stdev(sample)
        sample_size = len(sample)

        t_obt = (sample_mean - pop_mean) / math.sqrt(pop_var / sample_size)

        df = sample_size - 1

        print("""
                Single sample t-test results - all values rounded to 2 d.p.:
                T-obtained = {}
                Degrees of Freedom = {}
                Sample mean and standard deviation = {} ({})
                Population mean and variance = {} ({})
                """.format(round(t_obt, dp), df, round(sample_mean, dp), round(s1, dp), round(pop_mean, dp),
                           round(pop_var, dp)))

        return round(t_obt, dp), df, round(sample_mean, dp), round(pop_mean, dp)

    @staticmethod
    def independent_samples(exp_ctr):
        """
        Measures BP properties againts other NBP properties in that postcode
        :param exp_ctr: ([ls of experimental/exact bp values], [ls of control/area matches values])
        :return: t-obt, df, experimental mean, control mean
        """
        exp = exp_ctr[0]
        ctr = exp_ctr[1]
        xBar1 = statistics.mean(exp)
        s1 = statistics.stdev(exp)
        sumX1 = sum(exp)
        sumX1sqr = sum(map(lambda x: x * x, exp))
        n1 = len(exp)

        xBar2 = statistics.mean(ctr)
        s2 = statistics.stdev(ctr)
        sumX2 = sum(ctr)
        sumX2sqr = sum(map(lambda x: x * x, ctr))
        n2 = len(ctr)

        t_obt = (xBar1 - xBar2) / math.sqrt(
            (((sumX1sqr - ((sumX1 * sumX1) / n1)) + (sumX2sqr - ((sumX2 * sumX2) / n2))) /
             (n1 + n2 - 2)) * ((1 / n1) + 1 / n2)
        )

        df = (n1 - 1) + (n2 - 1)

        exp_xBar = xBar1
        ctr_xBar = xBar2

        print("""
        Independent samples t-test results - all values rounded to 2 d.p.:
        T-obtained = {}
        Degrees of Freedom = {}
        Blue plaques mean and standard deviation = {} ({})
        Non blue plaques mean and standard deviation = {} ({})
        """.format(round(t_obt, dp), df, round(exp_xBar, dp), round(s1, dp), round(ctr_xBar, dp), round(s2, dp)))

        return round(t_obt, dp), df, round(exp_xBar, dp), round(ctr_xBar, dp)


def runner(files, avg_prices, avg_type):
    """
    Runs all the 'save' methods to output the three data sets

    :param files: Data(csv, bp)
    :param avg_prices: stats dataframe
    :param avg_type: type of average to use
    :return:
    """
    # Repeated is dict of before and after installation average prices of a BP house
    repeated_measures_data = {}
    # Single sample is one list: sample prices. Pop var and mean are calculated sepetately
    single_sample_data = []
    # Independent samples is two lists: BP house prices and NBP prices that are in a BP postcode
    independent_samples_data = ([], [])

    for chunk in Data.read_csv(files, 6):
        single_sample_data.extend(Data.single_sample_save(files, chunk, avg_prices, avg_type))

        for person, bf_af in Data.repeated_measures_save(files, chunk, avg_prices, avg_type).items():
            # Just using update caused the keys to be replaced which is not good.
            if person in Data.repeated_measures_data.keys():
                # Add the new data
                repeated_measures_data[person]['Before'].extend(bf_af['Before'])
                repeated_measures_data[person]['After'].extend(bf_af['After'])
            else:
                repeated_measures_data.update({person: bf_af})

        # Stuff for independent samples t-test - basically properly updating the data
        data = (Data.independent_samples_save(files, chunk, avg_prices, avg_type))
        independent_samples_data[0].extend(data[0])
        independent_samples_data[1].extend(data[1])

    return repeated_measures_data, single_sample_data, independent_samples_data


@timer
def main(files, avg_type, shortcut=False):
    """
    Runs all t-tests
    :param files:
    :param shortcut:
    :param avg_type:
    :return: t-test results - printed out
    """

    print("""Beginning running of analysis...""")
    avg_prices = Data.house_prices_stats(files, shortcut)

    r, s, i = runner(files, avg_prices, avg_type)

    print('Calculating populations variance and mean')
    pop_var, pop_mean = population_variation(avg_prices)

    # Run t tests on the stuff
    print('Population mean and variance ', pop_mean, pop_var)
    return (TTests.repeated_measures(r)), \
           (TTests.single_sample(s, pop_var=pop_var, pop_mean=pop_mean)), \
           (TTests.independent_samples(i))


if __name__ == '__main__':
    csv_file = resources_file + 'pp-complete.csv'
    bp_file = resources_file + 'bp_csv.csv'
    files = Data(csv_file, bp_file)
    avgdf = Data.house_prices_stats(files, short_cut=True)
    main(files, 'median')
    main(files, 'mean')







# Two tailed test at .05 alpha
# T-obt hs to be larger than t-crit to be significant.

# Population mean and variance 1.00000350656 2.17564283699
#
# Repeated measures t - test results - all values rounded to 2 d.p.:
# T - obtained = 2.8, T-crit = 2.064 - Significant
# Degrees of Freedom = 24
# Before plaque installation mean and standard deviation = 1.45(1.12)
# After plaque installation mean and standard deviation = 1.26(1.05)
#
# Single sample t - test results - all values rounded to 2 d.p.:
# T - obtained = 14.46, T-crit (inf df)= 1.960 - Significant
# Degrees of Freedom = 707
# Sample mean and standard deviation = 1.80(1.70)
# Population mean and variance = 1.00(2.18)
#
# Independent samples t - test results - all values rounded to 2 d.p.:
# T - obtained = 1.63, T-crit (inf df)= 1.960 - Non significant
# Degrees of Freedom = 1680118
# Blue plaques mean and standard deviation = 1.44(1.04)
# Non blue plaques mean and standard deviation = 1.00(0.97)
#
# Time taken 4:27:14.44
#
# Repeated measures t-test and single sample t-test are both significant but independent samples t-test is not.
