#! /usr/local/bin/python3.7

"""
Task: connect the BP addresses to PP addresses. Once normalised, the BP address should map directly onto the
PP data set (PAON, Street, Postcode)

Solution: take the 'bp_normalised.csv' and 'pp_complete.csv' files and merge them to a 'merged_data.json'
This data is in the format
    {BP address: {PAON: {SAON: {before: {timestamp: weighted house price}

Ignore SAON, it will be split later during analysis.

Files
Exact BP address -- only the data for the exact BP addresses.
Postcode addresses -- pp addresses that are in a bp postcode -- todo
"""

import datetime
import pickle
import os

import blue_plaques.pp_metadata as metadata
import blue_plaques.tools as tools

resources_file = '{}/Resources'.format(os.path.dirname(os.path.dirname(__file__)))
pp_complete = f'{resources_file}/pp-complete.csv'

exact_link_json = f'{resources_file}/exact_link.pkl'
postcode_link_json = f'{resources_file}/postcode_link.pkl'

exact_link_extracted_file = f'{resources_file}/exact_bp_address_data.pkl'
postcode_link_extracted_file = f'{resources_file}/postcode_bp_address_data.pkl'


class ExactLinker:
    """
    Links exact addresses to pp-complete indexes
    {address: [list of index numbers], }
    """

    def __init__(self):
        self.pp = tools.read_pp()
        self.bp = tools.read_bp()

    def make_linked_dict(self):
        def get_pp_indexes_from_paon_pc(self, paon, postcode):
            ls = self.pp.index[(self.pp['Postcode'] == postcode) & (self.pp['PAON'] == paon)].tolist()
            return ls

        linked_dict = {}
        for index, row in self.bp.iterrows():
            address = row.address
            print(f'ExactLinker: {address}')
            paon = row.PAON
            postcode = row.Postcode
            indexes = get_pp_indexes_from_paon_pc(paon, postcode)
            linked_dict.update({address: indexes})
        return linked_dict

    @staticmethod
    def main():
        if os.path.exists(exact_link_json):
            return pickle.load(open(exact_link_json, 'rb'))
        else:
            linked_dict = ExactLinker().make_linked_dict()
            with open(exact_link_json, 'wb') as f:
                pickle.dump(linked_dict, f)
            return linked_dict


class PostcodeLinker:
    """
    For each BP postcode, gets all the PP indexes
    """
    def __init__(self):
        self.pp = tools.read_pp()
        self.bp = tools.read_bp()

    def get_pp_indexes_from_pc(self, postcode):
        return self.pp.index[(self.pp['Postcode'] == postcode)].tolist()

    @staticmethod
    def remove_bp_properties():
        """Get the BP properties index and remove them"""
        bp_indexes = []
        for address, indexes in ExactLinker.main().items():
            indexes.extend(indexes)
        return bp_indexes

    def make_linked_dict(self):
        linked_dict = {}
        for postcode in list(set(self.bp['Postcode'].tolist())):
            print(f'PostcodeLinker: {postcode}')
            indexes = self.get_pp_indexes_from_pc(postcode)
            linked_dict.update({postcode: indexes})
        return linked_dict

    @staticmethod
    def main(from_scratch=False):
        if os.path.exists(postcode_link_json) and from_scratch is False:
            return pickle.load(open(postcode_link_json, 'rb'))
        else:
            linked_dict = PostcodeLinker().make_linked_dict()
            with open(postcode_link_json, 'wb') as f:
                pickle.dump(linked_dict, f)
            return linked_dict


class ExtractBPAddressesData:
    """Exact BP data to {address: {paon: {saon: {sale date: weighted price}}} from {address: [ls of indexes]}
    Uses median outward code house price.
    :arg data_type - exact: only BP houses, postcode: all houses in BP postocdes
    """

    def __init__(self, data_type='exact'):
        if data_type == 'exact':
            self.linker_dict = ExactLinker.main()
        elif data_type == 'postcode':
            self.linker_dict = PostcodeLinker.main()
        else:
            raise TypeError('Needs data_type arg to be exact or postcode')
        self.pp = tools.read_pp()
        self.bp = tools.read_bp().set_index('address')
        self.metadata = metadata.load_meta_data()
        self.before_after_dict = {}  # See get_before_after_from_linker() for where it is used.

    @staticmethod
    def before_or_after_year(target_year: int, input_year: int):
        """Requires the year as an int to be inputted"""
        if (target_year - input_year) < 0:
            return 'before'
        elif (target_year - input_year) > 0:
            return 'after'
        elif (target_year - input_year) == 0:
            return 'same'
        else:
            return None

    def add_to_before_after_dict(self, address, paon, saon, before_or_after, sale_year, weighted_price):
        """Adds data to the before_after_dict"""
        if address not in self.before_after_dict.keys():
            self.before_after_dict.update({address: {}})
        if paon not in self.before_after_dict[address]:
            self.before_after_dict[address].update({paon: {}})
        if saon not in self.before_after_dict[address][paon]:
            self.before_after_dict[address][paon].update({saon: {'before': {}, 'after': {}}})

        self.before_after_dict[address][paon][saon][before_or_after].update({sale_year: weighted_price})

    def apply_weighted_price(self, price, outward_code, year):
        return price / self.metadata.loc[str(outward_code), int(year)]['median']

    def get_before_after_from_linker(self):
        """
        Dict file is: {BP address: [ls of pp-complete index numbers]}
        Take a list of indexes and split it into paon and then saon then pull the sale date and (weighted) price

        :return: {address: PAON: {SAON: {before: {date: price, }, 'after': {d: p, }}}}
        """
        # {address: {SAON: {before: {date: price, }, 'after': {d: p, }, SAON2: {}, address2:

        for address, ls_of_index in self.linker_dict.items():
            print(address)
            self.before_after_dict.update({address: {}})
            if len(ls_of_index) == 0:
                self.before_after_dict[address] = None
                continue

            # If running postcode wide, then there is no postcode in the bp file. But that postcode should exits...
            bp_year = datetime.datetime.strptime(self.bp.loc[address].year, '%d/%m/%Y').year  # int

            df = self.pp.loc[ls_of_index]  # NB: PAON and SAON are categories so no groupby
            for i, row in df.iterrows():
                paon = row.PAON
                saon = row.SAON
                sale_year = row.Date_sold
                outward_code = row.Outward_code
                price = row.Price
                weighted_price = self.apply_weighted_price(price, outward_code, sale_year.year)
                before_or_after = self.before_or_after_year(bp_year, sale_year.year)
                if before_or_after == 'same':
                    continue
                self.add_to_before_after_dict(address, paon, saon, before_or_after, sale_year, weighted_price)

        return self.before_after_dict

    def remove_bp_addresses_not_in_pp(self):
        addresses_to_remove = []
        outward_codes = list(set(self.pp['Outward_code'].tolist()))
        for address, row in self.bp.iterrows():
            if row.Postcode.split(' ')[0] in outward_codes is False:
                addresses_to_remove.append(address)
        self.bp = self.bp.drop(addresses_to_remove)

    def get_data(self):
        self.remove_bp_addresses_not_in_pp()
        self.get_before_after_from_linker()
        return self.before_after_dict

    @staticmethod
    def main(dtype, from_scratch=False):
        """
        Load if exists, otherwise make the data file.
        :param dtype: exact or postcode
        :param from_scratch: True is do the work again, False is load the file.
        :return:
        """

        if dtype == 'exact':
            if os.path.exists(exact_link_extracted_file) and from_scratch is False:
                with open(exact_link_extracted_file, 'rb') as f:
                    return pickle.load(f)
            else:
                dl = ExtractBPAddressesData(data_type=dtype).get_data()
                with open(exact_link_extracted_file, 'wb') as f:
                    pickle.dump(dl, f)
                return dl
        elif dtype == 'postcode':
            if os.path.exists(postcode_link_extracted_file) and from_scratch is False:
                with open(postcode_link_extracted_file, 'rb') as f:
                    return pickle.load(f)
            else:
                dl = ExtractBPAddressesData(data_type=dtype).get_data()
                with open(postcode_link_extracted_file, 'wb') as f:
                    pickle.dump(dl, f)
                return dl
        else:
            raise TypeError('dtype needs to be exact or postcode')


if __name__ == '__main__':
    print(ExtractBPAddressesData.main('postcode', from_scratch=False))
