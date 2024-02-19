#! /usr/local/bin/python3.6

import os
import unittest
import pandas as pd
import numpy as np

from blue_plaques.blue_plaques import analysis_3 as analysis


# Keep the testing functions independent of each other
# Ensure they don't need to be changed when the function it's testing is changed
#


class TestAnalysis3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Make a temp csv and bp txt file to have everything run on"""
        df = pd.DataFrame()
        data = [
            ['{0}', '100', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{1}', '200', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{2}', '300', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],

            ['{3}', '400', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{4}', '500', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{5}', '600', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{6}', '700', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '4', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{7}', '800', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '4', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],

            ['{8}', '900', '2014-01-01', 'N7 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{9}', '900', 'NaN', 'N7 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A', 'A',
             'GREATER LONDON', 'A'],
            ['{10}', '900', '2015-01-01', 'NaN', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON', 'A', 'A'],
            ['{11}', '900', '2016-01-01', 'N7 2NU', 'A', 'A', 'A', '2', '', 'NaN', 'NaN', 'A', 'A', 'GREATER LONDON',
             'A', 'A']
        ]
        df = df.append(data)

        df.columns = ['ID', 'Price', 'Date_sold', 'Postcode', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
                      'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
                      'Record_Status']

        pd.DataFrame.to_csv(df, '/tmp/csv_file.csv', index=False)

        cls.csv = '/tmp/csv_file.csv'

        # Make blue plaque file
        bpdata = [
            ['2 Hopping Lane\nIslington\nLondon, N1 2NU', 'Matt Barson', 'https://en.wikipedia.org/wiki//MattBarson',
             '2015'],
            ['4 Hopping Lane\nIslington\nLondon, N7 2NU', 'Chris Barson', 'https://en.wikipedia.org/wiki//MattBarson',
             '2015'],
            ['4 Hopping Lane\nIslington\nLondon, N7 2NU', 'Chris Barson', 'https://en.wikipedia.org/wiki//MattBarson',
             np.nan],
            ['4 Hopping Lane\nIslington\nLondon, N7 2NU', np.nan, 'https://en.wikipedia.org/wiki//MattBarson', '2015']
            ]
        bpdf = pd.DataFrame()
        bpdf = bpdf.append(bpdata)
        bpdf.columns = ['Address', 'Person', 'Wiki', 'Year']

        pd.DataFrame.to_csv(bpdf, '/tmp/bp.csv', index=False)
        cls.bp = '/tmp/bp.csv'

    @classmethod
    def tearDownClass(cls):
        """Delete bp and csv file"""
        os.remove(cls.csv)
        os.remove(cls.bp)

    def test_get_year(self):
        self.assertEqual(analysis.get_year('1995-08-09 00:00'), 1995)
        self.assertEqual(analysis.get_year(1995), 1995)
        self.assertEqual(analysis.get_year(pd.to_datetime('1995-08-09 00:00')), None)
        self.assertEqual(analysis.get_year('1995'), 1995)
        self.assertEqual(analysis.get_year('1970'), None)

        self.assertNotEqual(analysis.get_year('string'), 1995)

    def test_find_area(self):
        """Tests postcode splitter despite that it's not in the Data class"""
        self.assertEqual(analysis.find_area('N1 2NU'), 'N1')
        self.assertEqual(analysis.find_area('ALN 2NU'), 'ALN')
        self.assertEqual(analysis.find_area('N31 2NU'), 'N31')
        self.assertNotEqual(analysis.find_area('N 1 2NU'), 'N 1')
        self.assertEqual(analysis.find_area(np.nan), None)

    def test_read_csv(self):
        """Tests read csv
        Makes sure that the Data.read_csv method gets the correct headings from the right bits
        Read the first line of the csv and check it's all correct to what I think it is. """
        # ['ID', 'Price', 'Date_sold', 'Postcode', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
        #  'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
        #  'Record_Status']
        for chunk in analysis.Data.read_csv(analysis.Data(self.csv, self.bp), 3):
            self.assertEqual(len(chunk), 10)
            for row in chunk.itertuples():
                self.assertEqual(row.ID[0], '{')
                self.assertTrue(int(row.Price))
                self.assertRegex(row.Date_sold, '\d\d\d\d-\d\d-\d\d')
                self.assertRegex(row.Postcode, '[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}')

                if pd.isnull(row.Street) is True:
                    pass
                else:
                    self.assertEqual(row.Street, 'HOPPING LANE')

    def test_read_bp(self):
        """Read and check setUp bp csv file"""
        df = analysis.Data.read_bp(analysis.Data(self.csv, self.bp))
        # Manually check a few from the wiki
        # Check it's the right sort of thing
        for row in df.itertuples():
            self.assertTrue(type(str(row.Year)))
            self.assertRegex(row.Postcode, '[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}')
            self.assertEqual(type(row.Address_list), list)
            self.assertEqual(row.Address_list, ['Hopping Lane', 'Islington', 'London'])
        test_df = pd.DataFrame(
            [
                ['Matt Barson', 'https://en.wikipedia.org/wiki//MattBarson', '2015', '2',
                 ['Hopping Lane', 'Islington', 'London'], 'N1 2NU'],
                ['Chris Barson', 'https://en.wikipedia.org/wiki//MattBarson', '2015', '4',
                 ['Hopping Lane', 'Islington', 'London'], 'N7 2NU'],
                ['Chris Barson', 'https://en.wikipedia.org/wiki//MattBarson', np.nan, '4',
                 ['Hopping Lane', 'Islington', 'London'], 'N7 2NU'],
                [np.nan, 'https://en.wikipedia.org/wiki//MattBarson', '2015', '4',
                 ['Hopping Lane', 'Islington', 'London'], 'N7 2NU']
            ], columns=['Person', 'Wiki', 'Year', 'Number', 'Address_list', 'Postcode'])
        pd.testing.assert_frame_equal(df, test_df)

    def test_average_prices(self):
        """Tests average prices of setUp csv file"""
        # Make the self chunk for the analysis. Needs to be something that read_csv can handle.
        # Create a small data frame, convert it to a csv and then read it.
        avg = analysis.Data.mean_prices(analysis.Data(self.csv, self.bp), short_cut=False)

        df = pd.DataFrame([
            # area, year, n, sum, sd,    sumX^2, avg price
            ['N1', 2014, 5.0, 3000.0, 141.42, 1900000.0, 600.0],
            ['N1', 2017, 3.0, 600.0, 81.65, 140000.0, 200.0],
            ['N7', 2014, 1.0, 900.0, 0.00, 810000.0, 900.0],
            ['N7', 2016, 1.0, 900.0, 0.00, 810000.0, 900.0]
        ], columns=['Area', 'Year', 'Price_count_sum', 'Price_sum', 'SD', 'SumXSqr', 'Average_price'])
        pd.to_numeric((df['Price_count_sum'], df['Price_sum'], df['SD'], df['SumXSqr'], df['Average_price']),
                      errors='ignore')

        pd.testing.assert_frame_equal(avg, df)

    def test_exact_bp_matches(self):
        """Takes chunk and bp data
        Functions returns dataframe of EXACT matches - Person, Year, ID, Price, Date_sold"""
        files = analysis.Data(self.csv, self.bp)
        for chunk in analysis.Data.read_csv(files, 6):
            matches = analysis.Data.exact_bp_matches(files, chunk)
            correct = {'Matt Barson': ['{0}', '{1}', '{2}', '{3}', '{4}', '{5}']}
            self.assertEqual(matches, correct)

    def test_population_variation(self):
        """Tests the calculation of population variance and mean form source"""
        files = analysis.Data(self.csv, self.bp)
        avg = analysis.Data.mean_prices(files, short_cut=False)
        var, mean = analysis.population_variation(files, avg)
        self.assertEqual(var, 0.091420118343195259)
        self.assertEqual(mean, 1.0)

    # Now the Analysis method

    def test_repeated_measures_save(self):
        """Input is chunk, bp, avg_prices and returns a dict like
            {'Person name: {'Before': [ls before prices], 'After': [ls after prices]}}
        Takes land registry dataframe, extracts the bp houses. From that, extract the price for before and after BP
        installation.
        """
        files = analysis.Data(self.csv, self.bp)

        avg = pd.DataFrame([
            ['N1', 2017, 200],
            ['N1', 2014, 100]
        ])
        avg.columns = ['Area', 'Year', 'Average_price']

        for chunk in analysis.Data.read_csv(files, 6):
            dict = analysis.Data.repeated_measures_save(files, chunk, avg)
            self.assertEqual(dict, {'Matt Barson': {'Before': [4.0, 5.0, 6.0], 'After': [0.5, 1.0, 1.5]}})

    def test_single_sample_save(self):
        files = analysis.Data(self.csv, self.bp)

        avg = analysis.Data.mean_prices(files, short_cut=False)
        sample = []
        for chunk in analysis.Data.read_csv(files, 6):
            r = (analysis.Data.single_sample_save(files, chunk, avg))
            sample.extend(r)
        self.assertEqual(sample, [0.5, 1.0, 1.5])

    def test_independent_samples_save(self):
        """Tests it gives the correct data"""
        files = analysis.Data(self.csv, self.bp)
        avg = analysis.Data.mean_prices(files, short_cut=False)
        data = ([], [])
        for chunk in analysis.Data.read_csv(files, 6):
            stuff = analysis.Data.independent_samples_save(files, chunk, avg)
            data[0].extend(stuff[0])
            data[1].extend(stuff[1])
        self.assertEqual(data, ([0.5, 1.0, 1.5],
                                [1.167, 1.333, 1.0, 1.0]))

    def test_getRepeatesMeasuresTable(self):
        files = analysis.Data(self.csv, self.bp)

        # {'Matt Barson': {'Before': [4.0, 5.0, 6.0], 'After': [0.5, 1.0, 1.5]}}
        # ['Person', 'Postcode', 'Number', 'Year of BP installation', 'Weighted prices before', 'Weighted prices after']
        df = pd.DataFrame(
            [['Matt Barson', 'N1 2NU', '2', '2015', [0.666666666667, 0.833333333333, 1.0], [0.5, 1.0, 1.5]]])
        df.columns = (
            ['Person', 'Postcode', 'Number', 'Year of BP installation', 'Weighted_prices_before',
             'Weighted_prices_after'])

        table = analysis.Data.getRepeatesMeasuresTable(files, False)

        pd.testing.assert_frame_equal(table, df)

    def test_getAveragePricesTable(self):
        table = analysis.Data.getAveragePricesTable(analysis.Data(self.csv, self.bp), shortcut=False)


# Done
class TestTTests(unittest.TestCase):
    def test_repeated_measures_t_test(self):
        """Data gives known output of 7.706"""
        t_obt = analysis.TTests.repeated_measures({
            '1': {'Before': [165, 165], 'After': [145, 145]},
            '2': {'Before': [143], 'After': [137]},
            '3': {'Before': [175], 'After': [170]},
            '4': {'Before': [135], 'After': [136]},
            '5': {'Before': [148], 'After': [141]},
            '6': {'Before': [155], 'After': [138]},
            '7': {'Before': [158], 'After': [137]},
            '8': {'Before': [140], 'After': [125]},
            '9': {'Before': [172], 'After': [161]},
            '10': {'Before': [164], 'After': [156]},
            '11': {'Before': [178], 'After': [165]},
            '12': {'Before': [182], 'After': [170]},
            '13': {'Before': [190], 'After': [176]},
            '14': {'Before': [169], 'After': [154]},
            '15': {'Before': [157], 'After': [143]}
        })
        self.assertEqual(t_obt, (7.71, 14, 162.07, 150.27))
        self.assertEqual(analysis.TTests.repeated_measures(
            {'Matt Barson': {'Before': [0.66666666666666663, 0.83333333333333337, 1.0], 'After': [0.5, 1.0, 1.5]}})
            , 'Error - sample size too small, only one participant')
        self.assertEqual(analysis.TTests.repeated_measures({'Hello': 'Good bye', 'Hola': 'Estasß'}),
                         'Error - sample size too small, only one participant')

    def test_independent_samples_t_test(self):
        """Tests TTests.independent_samples_t_test for t-obt, df, experimental mean and control mean"""
        data = (
            [84, 78, 67, 87, 80, 78, 78, 79, 82, 81]
            ,
            [88, 97, 74, 80, 87, 90, 90, 86, 84, 78]
        )
        values = analysis.TTests.independent_samples(data)
        self.assertEqual(values, (-2.23, 18, 79.40, 85.40))

        # self.assertEqual(analysis.TTests.independent_samples(([], [])), )

    def test_single_sample_t_test(self):
        """Tests single sample t-test for t-obt, df, sample mean and pop mean.
        Uses an exact population variance so whole population data needed in single list to be used"""
        data = [7500, 7500, 7500, 7500, 7500, 7500, 7500, 7500, 7500]

        self.assertEqual(analysis.TTests.single_sample(data, pop_var=2250000, pop_mean=6500), (2.00, 8, 7500, 6500))


class TestMain(unittest.TestCase):
    def setUp(self):
        df = pd.DataFrame()
        data = [
            ['{0}', '100', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{1}', '200', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{2}', '300', '2017-01-01', 'N1 2NU', 'A', 'A', 'A', '4', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],

            ['{3}', '400', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{4}', '500', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{5}', '600', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '2', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{6}', '700', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '4', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{7}', '800', '2014-01-01', 'N1 2NU', 'A', 'A', 'A', '4', '', 'HOPPING LANE', 'Islington', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],

            ['{10}', '100', '2017-01-01', 'AL10 8RY', 'A', 'A', 'A', '2', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{11}', '200', '2017-01-01', 'AL10 8RY', 'A', 'A', 'A', '2', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{12}', '300', '2017-01-01', 'AL10 8RY', 'A', 'A', 'A', '4', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],

            ['{13}', '400', '2014-01-01', 'AL10 8RY', 'A', 'A', 'A', '2', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{14}', '500', '2014-01-01', 'AL10 8RY', 'A', 'A', 'A', '2', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{15}', '600', '2014-01-01', 'AL10 8RY', 'A', 'A', 'A', '2', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{16}', '700', '2014-01-01', 'AL10 8RY', 'A', 'A', 'A', '4', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{17}', '800', '2014-01-01', 'AL10 8RY', 'A', 'A', 'A', '4', '', 'BRIARS LANE', 'HATFIELD', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],

            ['{20}', '100', '2017-01-01', 'AL9 8RY', 'A', 'A', 'A', '2', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{21}', '200', '2017-01-01', 'AL9 8RY', 'A', 'A', 'A', '2', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{22}', '300', '2017-01-01', 'AL9 8RY', 'A', 'A', 'A', '4', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],

            ['{23}', '400', '2014-01-01', 'AL9 8RY', 'A', 'A', 'A', '2', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{24}', '500', '2014-01-01', 'AL9 8RY', 'A', 'A', 'A', '2', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{25}', '600', '2014-01-01', 'AL9 8RY', 'A', 'A', 'A', '2', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{26}', '700', '2014-01-01', 'AL9 8RY', 'A', 'A', 'A', '4', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A'],
            ['{27}', '8000', '2014-01-01', 'AL9 8RY', 'A', 'A', 'A', '4', '', 'LANE', 'HELLO', 'A', 'A',
             'GREATER LONDON',
             'A', 'A']

        ]
        df = df.append(data)

        df.columns = ['ID', 'Price', 'Date_sold', 'Postcode', 'Property_type', 'New_build', 'Estate_Type', 'PAON',
                      'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPD_Category',
                      'Record_Status']

        pd.DataFrame.to_csv(df, '/tmp/csv_file.csv', index=False)

        self.csv = '/tmp/csv_file.csv'

        # Make blue plaque file
        bpdata = [
            ['2 Hopping Lane\nIslington\nLondon, N1 2NU', 'Matt Barson', 'https://en.wikipedia.org/wiki/MattBarson',
             '2015'],
            ['2 Briars Lane\nHatfield\nLondon, AL10 8RY', 'Chris Barson', 'https://en.wikipedia.org/wiki/ChrisBarson',
             '2015'],
            ['2 Lane\nHello\nLondon, AL9 8RY', 'Jonathan Barson', 'https://en.wikipedia.org/wiki/JBarson', '2015']
        ]
        bpdf = pd.DataFrame()
        bpdf = bpdf.append(bpdata)
        bpdf.columns = ['Address', 'Person', 'Wiki', 'Year']

        pd.DataFrame.to_csv(bpdf, '/tmp/bp.csv', index=False)
        self.bp = '/tmp/bp.csv'

    def test_main(self):
        """Tests that main method is correct. It will take the defined data from class and give the repeated, single and
        independent t-test results"""
        files = analysis.Data(self.csv, self.bp)
        main = analysis.main(files, shortcut=False)
        self.assertEqual(main[0], (-0.57, 2, 0.64, 0.75))  # Repeated measures
        self.assertEqual(main[1], (-0.44, 5, 0.75, 1.0))  # Single sample
        self.assertEqual(main[2], (-0.5, 19, 0.75, 1.05))  # Independent samples


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestAnalysis3('test_average_prices'))

    return suite


if __name__ == '__main__':
    # runner = unittest.TextTestRunner()
    # runner.run(suite())
    unittest.main()
