#! /usr/local/bin/python3.7

"""
Aims of file -- to input a list of address IDs and return t-test outputs
Sub aims
    1. Convert IDs to needed info (prices over time)
    2. Do t-test (repeated measures is the aim for now)
        1. For overall mean before and after
        2. For overall median before and after
        3. For just before and just after
"""
import os
import statistics

import numpy as np
from blue_plaques import linker
from scipy import stats

resources = '{}/Resources'.format(os.path.dirname(os.path.dirname(__file__)))


class RepeatedMeasures:
    def __init__(self, average_type='median', area='exact', measurement='either_side'):
        if average_type not in ['mean', 'median']:
            raise TypeError('average type is not mean or median')
        else:
            self.average_type = average_type
        if area not in ['exact', 'postcode']:
            raise TypeError('area is not exact or postcode')
        else:
            self.area = area
        if measurement not in ['average', 'either_side']:
            raise TypeError('collapsing_type is not collapse or not_collapse')
        else:
            self.measurement = measurement
        self.before_after = linker.ExtractBPAddressesData.main(area)

    def convert_linker_to_lists(self):
        """Converts {address: {PAON: {SAON: {before: {date: price, }, 'after': {d: p, } to

        """
        results = []  # [{address: {'before': before, 'after': after}, ]
        for address, paon in self.before_after.items():
            if paon is None:
                continue
            for saon in paon.values():
                if saon is None:
                    continue
                for before_after in saon.values():
                    if len(before_after['before']) > 0 and len(before_after['after']) > 0:

                        if self.measurement == 'either_side':
                            before = (before_after['before'][max(before_after['before'].keys())])
                            after = (before_after['after'][min(before_after['after'].keys())])
                            results.append({address: {'before': before, 'after': after}})
                        elif self.measurement == 'average':
                            before = (statistics.mean(list(before_after['before'].values())))
                            after = (statistics.mean(list(before_after['after'].values())))
                            results.append({address: {'before': before, 'after': after}})
        return results

    def repeated_measures_t_test(self):
        results = self.convert_linker_to_lists()
        before = []
        after = []
        for address in results:
            for value in address.values():
                before.append(value['before'])
                after.append(value['after'])
        meana = round(float(np.mean(after)), 3)
        sda = round(statistics.stdev(list(after)), 3)

        meanb = round(float(np.mean(before)), 3)
        sdb = round(statistics.stdev(list(before)), 3)

        t, p = stats.ttest_rel(after, before, nan_policy='omit')
        t = round(t, 4)
        p = round(p, 3)
        df = float(len(after) - 1)

        return p, t, df, meana, sda, meanb, sdb

    def main(self):
        p, t, df, meana, sda, meanb, sdb = self.repeated_measures_t_test()
        print(f'p-value: {p}, t_obt: {t}, mean after (sd): {meana} ({sda}), mean before (sd): {meanb} ({sdb})')
        return p, t, df, meana, sda, meanb, sdb


if __name__ == '__main__':
    RepeatedMeasures('mean', 'exact', 'either_side').main()


## Old, need to try again.
# Repeated Measures t-test
# t-obt is -1.7442, p-value is 0.085
# df is 83.0 and before mean(sd) is 1.529(1.19) and after mean(sd) is 1.68(1.672)

# Postcode repeated measures
# p<0.001 (t = -7.7985), df is 5914 and before mean (SD) 1.323(0.952) and after mean (sd) 1.387(1.201).
