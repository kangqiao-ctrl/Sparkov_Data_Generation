# Generate Fake Credit Card Transaction Data, Including Fraudulent Transactions 

## General Usage

Please run the datagen script as follow:

```bash
python datagen.py -n <NUMBER_OF_CUSTOMERS_TO_GENERATE> -o <OUTPUT_FOLDER> <START_DATE> <END_DATE> -s -i
```

To see the full list of options, use:

```bash
python datagen.py -h
```

You can pass additional options with the following flags:

- `-config <CONFIG_FILE>`: pass the name of the config file, defaults to `./profiles/main_config.json`
- `-seed <INT>`: pass a seed to the Faker class
- `-c <CUSTOMER_FILE>`: pass the path to an already generated customer file
- `-o <OUTPUT_FOLDER>`: folder to save files into
- `-s`: whether generate merchants with static coordinates and identify high-risk merchants/enable new fraud scenarios (Newly added in v1.0b)
- `-i`:  mark all the scenario-generated transactions with scenario markers (Newly added in v1.0b)

## Static Merchants and Fraud Scenarios
The latest version v1.0b added a feature to generate static merchants with fixed coordinates. A couple of new fraud scenario are also provided. 

The customer's new behaviors are:

0. If the category of transaction is not online shopping, the customer will shop at the merchants within a 0.1 degree (11.1 km) radius;
1. The customer will drive further (0.5 degree, 55.5 km -- feel free to adjust it) if there is no nearby merchant and (a) the transaction category belongs to `brick_and_mortar` or (b) rolled under 30 even though the category is not in `brick_and_mortar`;
2. If there is still no available merchants, the customer will either (a) gave up shopping if the businesss is brick and mortar or (b) shop online for other type of businesses, and the transaction will be marked as online shopping. 

A brief work flow of how the static merchants and related fraud scenario is:

0. Shopping categories are associated with risk(i.e., 'high', 'moderate') and business type (i.e., 'online shopping', 'brick and mortar');
1. Total business number is correlated with customer number (`NB_CUSTOMERS`), and will be allocated based o the population in each activated city (i.e., city w/ at least 1 customer). Brick and mortar busines will have higher probability to be generated comparing to other categories.
2. When generating a specific merchant, depending on its risk, there is 1/5/10 percent chance for businesses in all/moderate risk/high risk categories to be compromised;
3. When a customer encountered (a) a compromised business or (b) belongs to a vulnerable group and shopped online, there is 10/5/3 percent chance (corresponds to high risk/vulerable + online/moderate risk) for this transaction to be compromised. If `-i` flag is added, the scenario will be marked in the generated dataset in `is_fraud` column. 

Note:

0. All the parameters mentioned above (i.e., percentages, amount of merchants) were tested under a `NB_CUSTOMER = 10000` setting and was targeting making sure: 
1. the dataset has a fraud transaction rate under 1% and greater than 1/1000, and 
2. no fraud transactions generated by any scenario is greater than those simply generated by unlucky customers. So please feel free to play around with those parameters in `datagen_static_merchants.py` and `datagen_transaction.py` whenever you found these the results in the dataset is not desirable. 
3. Currently, the new features will significantly slow down the generating process (Under 48 cores 1 million transaction speed: 8s vs 30min, 100-200x difference). Will try to optimize in the future.

These customer behaviors and fraud scenarios will be very helpful you need a dataset with a more complicated data generating process, which is one of the key concepts in causal inference research, or whenever you simply want some more authenticity in the synthetic data.

All these bew behaviors are optional, which means they are turned off by default. You can turn them on simply by adding a `-s` flag when running `datagen.py`. 

The generation code is originally based on code by [Josh Plotkin](https://github.com/joshplotkin/data_generation). Change log of modifications to original code are below.

## Change Log

### v1.0b

- Static merchants and new behaviors:
    - The generator can generate merchants with fixed coordinates(optional)
    - The program can acquire merchants within a certain radius of a specific customer
    - The customers will try their best to shop at merchants near them
    - Provide multiple fraud scenarios (compromised merchants & high/moderate fraudlent risk categories, online shopping & vulnerable groups), inspired by [Fraud Detection Handbook](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html)
    - The generator will also identify online transaction in the dataset now
- Miscellaneous:
    - The generator will randomize customer coordinates
    - Optimized the structure of the software, removed some unused .py and .json files and test modules
    - Provided a notebook for validating the newly added features

### v1.0

- Parallelized version, bringing orders of magnitude faster generation depending on the hardware used.

### v0.5

- 12x speed up thanks to some code refactoring.

### v0.4

- Only surface-level changes done in scripts so that simulation can be done using Python3
- Corrected bat files to generate transactions files.

### v0.3

- Completely re-worked profiles / segmentation of customers
- introduced fraudulent transactions
- introduced fraudulent profiles
- modification of transaction amount generation via Gamma distribution
- added 150k_ shell scripts for multi-threaded data generation (one python process for each segment launched in the background)

### v0.2

- Added unix time stamp for transactions for easier programamtic evaluation.
- Individual profiles modified so that there is more variation in the data.
- Modified random generation of age/gender. Original code did not appear to work correctly?
- Added batch files for windows users

### v0.1

- Transaction times are now included instead of just dates
- Profile specific spending windows (AM/PM with weighting of transaction times)
- Merchant names (specific to spending categories) are now included (along with code for generation)
- Travel probability is added, with profile specific options
- Travel max distances is added, per profile option
- Merchant location is randomized based on home location and profile travel probabilities
- Simulated transaction numbers via faker MD5 hash (replacing sequential 0..n numbering)
- Includes credit card number via faker
- improved cross-platform file path compatibility