__author__ = "Brandon Harris - brandonharris.io, Emmanuel Leroy - streamnsight & Qiao Kang - kangqiao-ctrl"
__license__ = "MIT License"
__version__ = "1.0b"

import argparse
import pathlib
import os
import json
from multiprocessing import Pool, cpu_count

import datagen_customer
from datagen_transaction import main as datagen_transactions
from datagen_static_merchants import main as datagen_static_merchants
from utilities import valid_date

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sparkov Card Fraud Dataset Generator')
    parser.add_argument('-n', '--nb_customers', type=int, help='Number of customers to generate', default=10)
    parser.add_argument('start_date', type=valid_date, help='Transactions start date')
    parser.add_argument('end_date', type=valid_date, help='Transactions start date')
    parser.add_argument('-seed', type=int, nargs='?', help='Random generator seed', default=42)
    parser.add_argument('-config', type=pathlib.Path, nargs='?', help='Profile config file (typically profiles/main_config.json")', default='./profiles/main_config.json')
    parser.add_argument('-c', '--customer_file', type=pathlib.Path, help='Customer file generated with the datagen_customer script', default=None)
    parser.add_argument('-o', '--output', type=pathlib.Path, help='Output Folder path', default='data')
    parser.add_argument('-s', '--static_merchants', action='store_true', help='Whether generate merchants with static coordinates and identify high-risk merchants') # Static merchants switch
    parser.add_argument('-i', '--scenario_identifier', action='store_true', help='Mark scenario-generated transactions with scenario markers') # If need seperate markers for transactions generated under different scenarios
    
    args = parser.parse_args()
    num_cust = args.nb_customers
    seed_num = args.seed
    config = args.config
    out_path = args.output
    customer_file = args.customer_file
    start_date = args.start_date
    end_date = args.end_date
    customers_out_file = customer_file or os.path.join('customers_merchants/customers.csv')
    is_static = bool(args.static_merchants)
    need_identifier = bool(args.scenario_identifier)

    # create the folder if it does not exist
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # if no customers file provided, generate a customers file
    if customer_file is None and num_cust is not None:
        if os.path.exists(customers_out_file):
            # prompt user to overwrite
            agree = input(f"File {customers_out_file} already exists. Overwrite? (y/N)")
            if agree.lower() != 'y':
                exit(1)
        datagen_customer.main(num_cust, seed_num, config, customers_out_file)
        
    elif customer_file is None:
        print('Either a customer file or a number of customers to create must be provided')
        exit(1)
    
    # if we're supplied with a customer file, we need to figure how many we have
    if customer_file is not None:
        num_cust = 0
        with open(customer_file, 'r') as f:
            for row in f.readlines():
                num_cust += 1

    if is_static: # If is_static is True, generate merchants with static coordinates and also the fraud transactions will be based on different scenario
        datagen_static_merchants(num_cust, datagen_customer.activated_cities_pos)

    # figure out reasonable chunk size
    num_cpu = cpu_count()
    print(f"Num CPUs: {num_cpu}")
    chunk_size = max(min(int(num_cust / 5), 1000), 1000 * int(num_cust / (1000 * num_cpu)))
    # because from one profile to another, there may be a 10-50x difference in size, it is best to use small
    # chunk sizes so as to spread the work across all CPUs. Bigger chunks means a core may process small profiles 
    # quickly and then be idle, while other cores process large profiles. Smaller chunks will run faster
    
    # zero padding determination
    zero_pad = len(str(num_cust - 1))

    # read config
    with open(config, 'r') as f:
        configs = json.load(f)

    profile_names = configs.keys()

    args_array = []
    for profile_file in configs.keys():
        customer_file_offset_start = 0
        customer_file_offset_end = min(num_cust - 1, chunk_size - 1)
        while customer_file_offset_start <= max(num_cust - 1, chunk_size):
            print(f"profile: {profile_file}, chunk size: {chunk_size}, \
                chunk: {customer_file_offset_start}-{customer_file_offset_end}")
            transactions_filename = os.path.join(out_path, 
                profile_file.replace('.json', 
                    f'_{str(customer_file_offset_start).zfill(zero_pad)}-{str(customer_file_offset_end).zfill(zero_pad)}.csv'))
            # Arguments need to be passed as a tuple
            args_array.append((
                customers_out_file, 
                pathlib.Path(os.path.join('profiles', profile_file)), 
                start_date, 
                end_date, 
                transactions_filename,
                customer_file_offset_start,
                customer_file_offset_end,
                is_static,
                need_identifier
            ))
            customer_file_offset_start += chunk_size
            customer_file_offset_end = min(num_cust - 1, customer_file_offset_end + chunk_size)

    with Pool() as p:
        p.starmap(datagen_transactions, args_array)
        