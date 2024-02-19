Module - blue_plaques
    plaque_scrape - Get the info off wikipedia
    analysis_3 - Run methods to get the necessary data we want
    plaque_scrape - gets data from wikipedia page
    test_analysis_3 - test file for analysis_3 - not yet got one for plaque_scrape
    __init__ - holds the two methods that are usable when running the method

Notes on the data analysis
    1. The weighted prices are done by year and as a proportion of the average price: weighted price = abs price / average  postcode price
    2. BP = blue plaques and NBP = non blue plaques, often referring to single houses

Repeated measured t-test
    Data - averaged before and after price of BP houses (weighted as a proportion of the area (e.g. N1)) sold
        NB - some data points were flats and some houses but no differentiation was made


Independent samples t-test
    Basically two lists of properties. One is BP properties and the other is BP properties within that postcode.
        Prices are weighted by area (N1)
    NBP


Single sample t-test - Test of a sample to the population
    Test of sample to the population: london prices vs bp prices (weighted)
    Exact bp houses vs all other houses.

From terminal you want to run
caffeinate python3 -c 'import blue_plaques; blue_plaques.from_download("land_reg csv", "blue plaque csv")'
or run
caffeinate python3 -c 'import blue_plaques; blue_plaques.from_scratch("/Path/to/an/empty/folder")'

The land reg data and bp data are both being included in the file for you to use.

Any issues, email matt.barson@gmail.com
Code is free and open source so feel free to use it but please notify me if you find any bugs or flaws in the code.