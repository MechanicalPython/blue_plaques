# blue_plaques

## Data inputs

### pp-complete.csv

Columns for the pp-complete.csv
Unique ID, Price,   Date sold,Postcode,
Property type, (D = Detached, S = Semi-Detached, T = Terraced, F = Flats/Maisonettes, O = Other )
New build, Estate type, PAON, SAON, Street/Road, Locality, Town/City, District, County, PPD Category, Record Status

File from  https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads

### Wiki_bp_data.csv

Pulled from Wikipedia by plaque_scrape.py 

Csv headers are address, person, wiki, year, person_year 

## Data Normalisation

The BP data is semi-automated by bp_adddress_normalisation.py that pulls the PAON and Postcode from the address which has to be then manually checked and corrected (use pp_lookup.py to help)

## Data Linking

Then the data is linked by linker.py {BP address: {PAON: {SAON: {sale_date: weighted price}}}}.
The price of the house is weighted to create a ratio of the house against the median house price for that outward code (using pp_metadata.py)

## T-tests

The main t-tests used is a repeated measures t-test that takes the before and after price of a BP house.
Assumption: the BP is placed on the PAON, not the SAON so all SAONs in an address are equally affected by the BP.
The 'before/after' can be either_side or average: the closest two sales around the BP installation or average of all before and all after.

Repeated measures t-test
​    Repeated measures is a test of the same house before and after a plaque is installed.

Independent samples t-test
​    Measures blue plaque properties against other properties in that postcode. Two samples from the same population.
​    The population is the area of the houses (e.g. N1) and the two conditions are plaque houses and all other houses.

Single sample t-test
​    Measures a sample against the population. Took all houses that had blue plaques on it, both before and after it obtained the plaque, and compared that to the population of London houses.



Make a new column in the PP dataset: does it match a BP address or postcode. 



## Notes on data

House prices are not normally distributed so median is used for pp_metadata.





For each house in BP addresses:

​	what are the IDs in the postcode

​	what are the IDs that exactly match







Collection: Plaque scrape, bp normalisation and linker

Analysis: fame and t-tests



