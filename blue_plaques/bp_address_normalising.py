#! /usr/local/bin/python3.7

"""
Get the PAON, street and Postcode from an address.
"""

import os
import re

from blue_plaques import plaque_scrape
from blue_plaques import tools

resources = '{}/Resources/'.format(os.path.dirname(os.path.dirname(__file__)))


class Normalise:
    def __init__(self, input_addresses):
        self.input_address = input_addresses
        self.pp = tools.read_pp()

    @staticmethod
    def get_postcode(address):
        pc = re.findall(r'[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}', address)
        if len(pc) == 0:
            return None
        else:
            return pc[0].strip()

    def get_paon(self, address):
        postcode = self.get_postcode(address)
        address = address.upper().replace(postcode, '').strip()

        if re.match(r'[0-9]+ ?- ?[0-9]+', address):  # num - num
            a, b = re.match(r'[0-9]+ ?- ?[0-9]+', address)[0].split('-')
            return f'{a.strip()} - {b.strip()}'.strip()

        elif re.match(r'[0-9]+[A-Z]? ', address):  # num or num letter
            return re.match(r'[0-9]+[A-Z]? ', address)[0].strip()

        elif re.match(r'[A-Z ]+, [0-9]+ ?- ?[0-9]+', address):  # name, num/num-num
            a, b = re.search(r'[0-9]+ ?- ?[0-9]+', address)[0].split('-')
            return f'{re.match(r"[A-Z ]+,", address)[0]} {a.strip()} - {b.strip()}'

        elif re.match(r'[A-Z ]+, [0-9]+ ', address):  # name, num/num-num
            return f'{re.match(r"[A-Z ]+, [0-9]+ ", address)[0]}'.strip()

        else:
            paons = list(self.pp.at[self.get_postcode, 'PAON'])
            for paon in paons:
                if paon in address:
                    return paon
        return None

    def get_street(self, address):
        address = address.upper()
        streets = list(self.pp.at[self.get_postcode, 'Street'])
        streets = [x for x in streets if str(x) != 'nan']

        if len(streets) == 1:
            return streets[0]

        for street in streets:
            if street.replace("'", '') in address.replace("'", ''):
                return street
        return None

    def parse_address(self, address):
        """
        Gets the paon, street and postcode from an address
        :return:
        """
        postcode = self.get_postcode(address)
        street = self.get_street(address)
        house_number = self.get_paon(address)

        return house_number, street, postcode

    def normalise_raw_bp_wiki_data(self):
        bp = plaque_scrape.load_wiki_data()
        numbers = []
        streets = []
        pcs = []
        for address in self.input_address:
            n, s, p = self.parse_address(address)
            numbers.append(n)
            streets.append(s)
            pcs.append(p)
        bp['PAON'] = numbers
        bp['Street'] = streets
        bp['Postcode'] = pcs
        return bp

    def main(self):
        addresses = tools.read_bp()['address'].tolist()
        bp = Normalise(addresses).normalise_raw_bp_wiki_data()
        bp.to_csv(tools.read_bp.__defaults__[0])


if __name__ == '__main__':
    main()
