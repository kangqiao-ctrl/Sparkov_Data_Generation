# Generate Fake Credit Card Transaction Data, Including Fraudulent Transactions 

## General Usage

Please run the datagen script as follow:

```bash
python datagen.py -n -s <NUMBER_OF_CUSTOMERS_TO_GENERATE> -o <OUTPUT_FOLDER> <START_DATE> <END_DATE> 
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

The generation code is originally based on code by [Josh Plotkin](https://github.com/joshplotkin/data_generation). Change log of modifications to original code are below.

## Change Log

### v1.0b

- New functions:
    - Add optionl static merchants profile generation
    - Provide MORE fraud scenarios (compromised merchants & high/moderate fraudlent risk categories, online shopping & vulnerable groups), inspired by [Fraud Detection Handbook](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html) 
    - Provide new logic to randomize customer/merchants coordinates
- Optimized the structure of the software, removed some unused .py and .json files and test modules
- Provided a notebook for checking the newly added features

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