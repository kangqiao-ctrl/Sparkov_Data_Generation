###
# Generates n merchants per category, to be piped into demographic_data/merchants_static.csv
###
__author__ = 'Brandon Harris - brandonharris.io'
from faker import Factory
from math import ceil
import sys, random
from datagen_customer import randomize_coordinate

fake = Factory.create('en_US')
cust_merchants_path = "./data/merchants_static.csv"

header = "category|merchant_name|lat|long|fraud_risk"
category_list = ["gas_transport",
                 "grocery_net",
                 "grocery_pos",
                 "pharmacy",
                 "misc_net",
                 "misc_pos",
                 "shopping_net",
                 "shopping_pos",
                 "utilities",
                 "entertainment",
                 "food_dining",
                 "health_fitness",
                 "home",
                 "kids_pets",
                 "personal_care",
                 "travel"]

safe_cates = ['pharmacy','health_fitness','home','kids_pets','personal_care','travel']

def main(n_customers, addy_list):

    if n_customers <= 200:
        coef = 5
    else:
        coef = 1

    total_number = n_customers * coef
    
    freq_n_coordinates = {}
    pop_sum = 0

    for city in addy_list:
        freq_n_coordinates[city[2]] = [int(city[5]),(float(city[3]),float(city[4]))]
        pop_sum += int(city[5])


    # setup output to file by redirecting stdout
    original_sys_stdout = sys.stdout
    if cust_merchants_path is not None:
        f_out = open(cust_merchants_path, 'w')
        sys.stdout = f_out

    print(header)

    for city in freq_n_coordinates:
        freq_n_coordinates[city][0] = freq_n_coordinates[city][0]/pop_sum
        city_merchant_number =  ceil(total_number * freq_n_coordinates[city][0])
        category_merchant_number = ceil(city_merchant_number/len(category_list))

        for c in category_list:
            for _ in range(category_merchant_number):
                merchant_fraud_flag = random.randint(0,100) 
                if merchant_fraud_flag <= 1 or (merchant_fraud_flag <= 5 and c not in safe_cates):
                    fraud_risk = 1
                else:
                    fraud_risk = 0
                print(f"{c}|{fake.company()}|{'|'.join(randomize_coordinate(*freq_n_coordinates[city][1],0.5))}|{fraud_risk}")
    
    # restore original sdtout when done
    if cust_merchants_path is not None:
        sys.stdout = original_sys_stdout