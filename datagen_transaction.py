import argparse
import csv
import json
import pathlib
import random
import sys
from datetime import timedelta

from faker import Faker
import numpy as np

from datagen_customer import headers
from datagen_static_merchants import high_risk_cates, moderate_risk_cates, online_shopping, brick_and_mortar
from profile_weights import Profile
from utilities import valid_date

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
    'merch_long',
    'is_online'
]

merchants = {} # A global variable to store returned merchants from read_merchants()

def read_merchants(static = False):
    # read file to merchant variable only once / built a map of merchant per category for easy lookup
    if static:
        merchants_path = 'customers_merchants/merchants_static.csv'
    else:
        merchants_path = 'customers_merchants/merchants.csv'
    with open(merchants_path, 'r') as merchants_file:
        csv_reader = csv.reader(merchants_file, delimiter='|')
        # skip header
        csv_reader.__next__()
        for row in csv_reader:
            if merchants.get(row[0]) is None:
                merchants[row[0]] = []
            if static:
                merchants[row[0]].append([row[1],row[2],row[3],row[4]])
            else:
                merchants[row[0]].append(row[1])

def get_list_terminals_within_radius(cust_lat, cust_long, merchant_list, r): 

        # Inspired by: https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html
        # Use numpy arrays in the following to speed up computations
        # Location (x,y) of customer as numpy array
    customer_lat_long = np.array([float(cust_lat), float(cust_long)])

    merch_coordinates = []
    for merch in merchant_list:
        merch_coordinates.append([float(merch[1]), float(merch[2])])
    merch_coordinates =  np.array(merch_coordinates)

    # Squared difference in coordinates between customer and terminal locations
    squared_diff = np.square(customer_lat_long - merch_coordinates)
    
    # Sum along rows and compute suared root to get distance
    dist = np.sqrt(np.sum(squared_diff, axis=1))
    
    # Get the indices of terminals which are at a distance less than r
    available_idx = list(np.where(dist<r)[0])

    # Get a list of available merchants
    available_merchants = [merchant_list[idx] for idx in available_idx]

    return available_merchants

class Customer:
    def __init__(self, raw):
        self.raw = raw.strip().split('|') # Customer attributes
        self.attrs = self.parse_customer(raw)
        self.fraud_dates = []

    def print_trans(self, trans, is_fraud, fraud_dates, static = False, scenario_identifier = False):

        is_traveling = trans[1] # Always NO in the current version. TODO in the future.
        travel_max = trans[2]

        # not traveling, so use 1 decimial degree (~70mile) radius around home address
        rad = 1
        if is_traveling:
            # hacky math.. assuming ~70 miles per 1 decimal degree of lat/long
            # sorry for being American, you're on your own for kilometers.
            rad = (float(travel_max) / 100) * 1.43

        for t in trans[0]: 
            # Each t is a list: [trans#, date, time, transaction number, category, amount, is_fraud]
            cate = t[4]
            merchants_in_category = merchants.get(cate) 

            cust_lat = self.attrs['lat']
            cust_long = self.attrs['long']

            is_online = 0
        
            if static:
                # All the print() which commented out can be uncommented for debugging. Remember to change sys.stdout accordingly.
                if cate in online_shopping: 
                    #print(f"Online shopping for {self.raw}, cate: {cate}.") # Such helper prints can be added whenever needed. 
                    is_online = 1
                else:
                    available_merchants = get_list_terminals_within_radius(cust_lat, cust_long, merchants_in_category, 0.1) # Default radius: 0.1 degree
                    if available_merchants: select_merchant_instance = random.sample(available_merchants, 1)[0]
                    else:
                        im_driving = random.randint(1,100)
                        if (im_driving <= 30 or cate in brick_and_mortar):  # If rolled under 30 or the category is brick_and_mortar, search at a higher radius (e.g., 0.5 degree).
                            #print(f" No available merchant in the city. If driving: {im_driving}; Category: {cate};  Customer: {self.raw}")
                            available_merchants = get_list_terminals_within_radius(cust_lat, cust_long, merchants_in_category, 0.5)
                            if available_merchants: 
                                #print(f"Found some merchants after driving!")
                                select_merchant_instance = random.sample(available_merchants, 1)[0]
                            elif cate in brick_and_mortar:
                                #print(f"No brick-n-mortar store in {cate} is available for this customer. Won't shop at this time")
                                continue
                            else:
                                #print(f"Drove for an extra 0.4 degree and no chance. Deided to go shopping online.")
                                is_online = 1
                        else:
                            is_online = 1
                if is_online:
                    select_merchant_instance = random.sample(merchants_in_category, 1)[0] # If the category is in online_shopping, do not bother finding the merchants near customer

                # If the merchant is compromised or the transaction happend online and the customer is of 50+ age:
                if select_merchant_instance[3] == '1' or (is_online and ('50up' in self.raw[-1])): 
                    merchant_fraud_flag = random.randint(1,100)

                    # A variable to save the conditions to trigger three different scenarios. Specifically:
                    # "High risk merchants" and no olled under 10;
                    # "Moderate risk merchants" and rolled under 3;
                    # Customer age under 50 and shopped online and rolled under 5.
                    scenario_flag = 'risk:high' if (cate in high_risk_cates and merchant_fraud_flag <= 10) else 'risk:moderate' if (cate in moderate_risk_cates and merchant_fraud_flag <= 3)\
                        else 'group:vulnerable' if (('50up' in self.raw[-1] and is_online) and merchant_fraud_flag <= 5) else None

                    if  scenario_flag: # If the scenario_flag is not None
                        #print(f"Encountered risky merchant! Cate: {cate}, Risk: {risk(cate)}, If 50+:{'50up' in self.raw[-1]}, Rolled {merchant_fraud_flag}.")
                        is_fraud = 1
                        if scenario_identifier:
                            t[6] = scenario_flag # Directly use the scenario_flag as the transaction identifier
                        else:
                            t[6] = 1 # Simply save ordinary flag int 1 to mark fraud transactions
                        #print('Fraud due to transaction at risky merchant/online.')

                chosen_merchant, merch_lat,  merch_long = select_merchant_instance[0], select_merchant_instance[1], select_merchant_instance[2]
            else:
                chosen_merchant = random.sample(merchants_in_category, 1)[0]
                merch_lat = fake.coordinate(center=float(cust_lat),radius=rad) 
                merch_long = fake.coordinate(center=float(cust_long),radius=rad)

            if (is_fraud == 0 and t[1] not in fraud_dates) or is_fraud == 1: 
                features = self.raw + t + [chosen_merchant, str(merch_lat), str(merch_long), str(is_online)]
                print("|".join(features)) # Final output print


    def parse_customer(self, line):
        # separate into a list of attrs
        cols = [c for c in line.strip().split('|')]
        # create a dict of name: value for each column
        return dict(zip(headers, cols))

def main(customer_file, profile_file, start_date, end_date, out_path=None, start_offset=0, end_offset=sys.maxsize, is_static = False, need_identifier = False):

    profile_name = profile_file.name
    profile_file_fraud = pathlib.Path(*list(profile_file.parts)[:-1] + [f"fraud_{profile_name}"]) 

    read_merchants(is_static)

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
                    fraud_flag = random.randint(1,100) # set fraud flag here, as we either gen real or fraud, not both for the same day. 
                    fraud_dates = []
                    # decide if we generate fraud or not
                    if fraud_flag <= 10: #11->25 Original percentage: 99%, which implies almost everybody will encounter fraud at least for once
                        fraud_interval = random.randint(1,1) 
                        # rand_interval is the random no of days to be added to start date
                        rand_interval = random.randint(1, inter_val)
                        #random start date is selected
                        newstart = start_date + timedelta(days=rand_interval)   
                        # based on the fraud interval , random enddate is selected
                        newend = newstart + timedelta(days=fraud_interval)
                        # we assume that the fraud window can be between 1 to 7 days 
                        fraud_profile.set_date_range(newstart, newend)
                        is_fraud = 1
                        temp_tx_data = fraud_profile.sample_from(is_fraud) # Sample with weights in the fraud*.json files
                        fraud_dates = temp_tx_data[3] 
                        cust.print_trans(temp_tx_data, is_fraud, fraud_dates, static = is_static, scenario_identifier = need_identifier) 

                    # we're done with fraud (or didn't do it) but still need regular transactions
                    # we pass through our previously selected fraud dates (if any) to filter them
                    # out of regular transactions
                    
                    is_fraud = 0
                    temp_tx_data = profile.sample_from(is_fraud)
                    cust.print_trans(temp_tx_data, is_fraud, fraud_dates, static = is_static, scenario_identifier = need_identifier)
                line_num += 1
                if line_num > end_offset:
                    break

    if out_path is not None:
        sys.stdout = original_sys_stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sparkov: Transaction Generator Module')
    parser.add_argument('customer_file', type=pathlib.Path, help='Customer file generated with the datagen_customer script')
    parser.add_argument('profile', type=pathlib.Path, help='profile')
    parser.add_argument('start_date', type=valid_date, help='Transactions start date')
    parser.add_argument('end_date', type=valid_date, help='Transactions start date')
    parser.add_argument('-o', '--output', type=pathlib.Path, help='Output file path')
    parser.add_argument('-s', '--static_merchants', action='store_true', help='Whether generate merchants with static coordinates and identify high-risk merchants') # Static merchants switch
    parser.add_argument('-i', '--scenario_identifier', action='store_true', help='Mark scenario-generated transactions with scenario markers')

    args = parser.parse_args()

    customer_file = args.customer_file
    profile_file = args.profile 
    start_date = args.start_date
    end_date = args.end_date
    out_path = args.output
    if_static = bool(args.static_merchants)
    need_identifier = bool(args.scenario_identifier)

    main(customer_file, profile_file, start_date, end_date, out_path, static = if_static, scenario_identifier=need_identifier)
    