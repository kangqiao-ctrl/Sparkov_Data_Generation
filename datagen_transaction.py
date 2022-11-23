import argparse
import csv
import json
import pathlib
import random
import sys
from datetime import datetime, timedelta

from faker import Faker
import numpy as np

from datagen_customer import headers
from profile_weights import Profile

fake = Faker()
transaction_headers = [
    'trans_num', 
    'trans_date', 
    'trans_time',
    'unix_time', 
    'category', 
    'amt', 
    'is_fraud', 
    'merchant', 
    'merch_lat', 
    'merch_long'
]

# Global merchant dict var
merchants = {}



class Customer:
    def __init__(self, raw):
        self.raw = raw.strip().split('|') # Customer attributes
        self.attrs = self.parse_customer(raw)
        self.fraud_dates = []

    def get_list_terminals_within_radius(self, cust_x_coordinate, cust_y_coordinate, merchant_list, r): 

        # From: https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html
    
        # Use numpy arrays in the following to speed up computations
        # Location (x,y) of customer as numpy array
        x_y_customer = np.array([float(cust_x_coordinate), float(cust_y_coordinate)])

        merch_coordinates = []
        for merch in merchant_list:
            merch_coordinates.append([float(merch[1]), float(merch[2])])
        merch_coordinates =  np.array(merch_coordinates)

        # Squared difference in coordinates between customer and terminal locations
        squared_diff_x_y = np.square(x_y_customer - merch_coordinates)
        
        # Sum along rows and compute suared root to get distance
        dist_x_y = np.sqrt(np.sum(squared_diff_x_y, axis=1))
        
        # Get the indices of terminals which are at a distance less than r
        available_idx = list(np.where(dist_x_y<r)[0])
        
        available_merchants = [merchant_list[idx] for idx in available_idx]
        # Return the list of terminal IDs
        return available_merchants

    def print_trans(self, trans, is_fraud, fraud_dates, static = False):
        is_traveling = trans[1] # KQ: Always NO in the current version
        travel_max = trans[2]

        # not traveling, so use 1 decimial degree (~70mile) radius around home address
        rad = 1
        if is_traveling:
            # hacky math.. assuming ~70 miles per 1 decimal degree of lat/long
            # sorry for being American, you're on your own for kilometers.
            rad = (float(travel_max) / 100) * 1.43

        for t in trans[0]: 
            # Each t is a list: [trans#, date, time, transaction number, category, amount, is_fraud]
            ## Get transaction location details to generate appropriate merchant record
            merchants_in_category = merchants.get(t[4]) # merchant category

            cust_lat = self.attrs['lat']
            cust_long = self.attrs['long']
        
            if not static:
                chosen_merchant = random.sample(merchants_in_category, 1)[0]
                merch_lat = fake.coordinate(center=float(cust_lat),radius=rad) 
                merch_long = fake.coordinate(center=float(cust_long),radius=rad)

            else:
                available_merchants = self.get_list_terminals_within_radius(cust_lat, cust_long, merchants_in_category, 0.1)
                if available_merchants == []:
                    select_merchant_instance = random.sample(merchants_in_category, 1)[0]
                else:
                    select_merchant_instance = random.sample(available_merchants, 1)[0]

                if select_merchant_instance[3] == '1':
                    merchant_compromise_flag = random.randint(0,100)
                    if merchant_compromise_flag <= 5:
                        is_fraud = 1
                        t[6] = 'x' # An intuitive check if the compromised merchant setting is working

                chosen_merchant, merch_lat,  merch_long = select_merchant_instance[0], select_merchant_instance[1], select_merchant_instance[2]

            if (is_fraud == 0 and t[1] not in fraud_dates) or is_fraud == 1: 
                features = self.raw + t + [chosen_merchant, str(merch_lat), str(merch_long)]
                print("|".join(features)) # Final output print


    def parse_customer(self, line):
        # separate into a list of attrs
        cols = [c for c in line.strip().split('|')]
        # create a dict of name: value for each column
        return dict(zip(headers, cols))

def valid_date(s):
    try:
        return datetime.strptime(s, "%m-%d-%Y")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


def main(customer_file, profile_file, start_date, end_date, out_path=None, start_offset=0, end_offset=sys.maxsize, static = False):

    # read file to merchant variable only once / built a map of merchant per category for easy lookup

    if not static:
        with open('data/merchants.csv', 'r') as merchants_file:
            csv_reader = csv.reader(merchants_file, delimiter='|')
            # skip header
            csv_reader.__next__()
            for row in csv_reader:
                if merchants.get(row[0]) is None:
                    merchants[row[0]] = []
                merchants[row[0]].append(row[1])
    else:
        with open('data/merchants_static.csv', 'r') as merchants_file:
            csv_reader = csv.reader(merchants_file, delimiter='|')
            # skip header
            csv_reader.__next__()
            for row in csv_reader:
                if merchants.get(row[0]) is None:
                    merchants[row[0]] = []
                merchants[row[0]].append([row[1],row[2],row[3],row[4]])

    profile_name = profile_file.name
    profile_file_fraud = pathlib.Path(*list(profile_file.parts)[:-1] + [f"fraud_{profile_name}"]) 

    # setup output to file by redirecting stdout
    original_sys_stdout = sys.stdout
    if out_path is not None:
        f_out = open(out_path, 'w')
        sys.stdout = f_out

    with open(profile_file, 'r') as f:
        profile_obj = json.load(f)
    with open(profile_file_fraud, 'r') as f:
        profile_fraud_obj = json.load(f)

    profile = Profile({**profile_obj}) 
    profile.set_date_range(start_date, end_date)
    fraud_profile = Profile({**profile_fraud_obj})

    inter_val = (end_date - start_date).days - 7
    # for each customer, if the customer fits this profile
    # generate appropriate number of transactions

    with open(customer_file, 'r') as f:
        f.readline()
        print("|".join(headers + transaction_headers))
        line_num = 0
        fail = False
        # skip lines out of range
        while line_num < start_offset:
            try:
                f.readline()
                line_num += 1
            except EOFError:
                # end of file?
                fail = True
                break
        if not fail:
            for row in f.readlines():
                cust = Customer(row)
                if cust.attrs['profile'] == profile_name:
                    is_fraud = 0
                    fraud_flag = random.randint(0,100) # Original comment: set fraud flag here, as we either gen real or fraud, not both for
                                            # the same day. 
                    fraud_dates = []
                    # decide if we generate fraud or not
                    if fraud_flag < 10: #11->25 Original: 99%
                        fraud_interval = random.randint(1,1) #7->1
                        # rand_interval is the random no of days to be added to start date KQ: Now been fixed to 1 day
                        rand_interval = random.randint(1, inter_val)
                        #random start date is selected
                        newstart = start_date + timedelta(days=rand_interval)   
                        # based on the fraud interval , random enddate is selected
                        newend = newstart + timedelta(days=fraud_interval)
                        # we assume that the fraud window can be between 1 to 7 days #7->1
                        fraud_profile.set_date_range(newstart, newend)
                        is_fraud = 1
                        temp_tx_data = fraud_profile.sample_from(is_fraud) # Sample with weights in the fraud*.json files
                        fraud_dates = temp_tx_data[3] 
                        cust.print_trans(temp_tx_data, is_fraud, fraud_dates, static) 

                    # we're done with fraud (or didn't do it) but still need regular transactions
                    # we pass through our previously selected fraud dates (if any) to filter them
                    # out of regular transactions
                    
                    is_fraud = 0
                    temp_tx_data = profile.sample_from(is_fraud)
                    cust.print_trans(temp_tx_data, is_fraud, fraud_dates, static)
                line_num += 1
                if line_num > end_offset:
                    break

    if out_path is not None:
        sys.stdout = original_sys_stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Transaction Generator')
    parser.add_argument('customer_file', type=pathlib.Path, help='Customer file generated with the datagen_customer script')
    parser.add_argument('profile', type=pathlib.Path, help='profile')
    parser.add_argument('start_date', type=valid_date, help='Transactions start date')
    parser.add_argument('end_date', type=valid_date, help='Transactions start date')
    parser.add_argument('-o', '--output', type=pathlib.Path, help='Output file path')

    args = parser.parse_args()

    customer_file = args.customer_file
    profile_file = args.profile 
    start_date = args.start_date
    end_date = args.end_date
    out_path = args.output

    main(customer_file, profile_file, start_date, end_date, out_path)

    