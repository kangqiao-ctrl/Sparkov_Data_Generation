### Generates merchants with fixed coordinates and piped into customers_merchants/merchants_static.csv

from faker import Factory
from math import ceil
import sys, random
from utilities import randomize_coordinate

fake = Factory.create('en_US')
cust_merchants_path = "./customers_merchants/merchants_static.csv"

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

high_risk_cates = ["gas_transport"]
moderate_risk_cates = ["misc_net","misc_pos","shopping_net","food_dining"]
online_shopping = ["grocery_net","misc_net","shopping_net","utilities"]
brick_and_mortar = ["gas_transport","food_dining"]


def main(n_customers, addy_list):

    if n_customers <= 1000:
        coef = 5 # For each customer, generate roughly 5 merchants if customers are less than 1000.
    else:
        coef = 1 # For each customer, generate roughly 1 merchants if customers
                 # are more than 1000. Due to we ceil() the allocated merchant numbers, 
                 # in reality this will give ~10 merchants per customer.

    total_number = n_customers * coef # Total number of the merchants
    
    freq_n_coordinates = {}
    pop_sum = 0

    for city in addy_list:
        # Save the cdf of each city in a dictionary, with [population, lat, long] as value
        freq_n_coordinates[city[2]] = [int(city[5]),(float(city[3]),float(city[4]))]
        # Calculate the total population in this round of simulation (population sum for all the activated cities)
        pop_sum += int(city[5])


    # setup output to file by redirecting stdout
    original_sys_stdout = sys.stdout
    if cust_merchants_path is not None:
        f_out = open(cust_merchants_path, 'w')
        sys.stdout = f_out

    print(header)

    for city in freq_n_coordinates:
        freq_n_coordinates[city][0] = freq_n_coordinates[city][0]/pop_sum # Now the value is: [population divided by total_population, lat, long]
        city_merchant_number =  ceil(total_number * freq_n_coordinates[city][0]) # Calculate the total merchant number of the city in all the categories
        # For brick and mortar businesses (e.g., gas, restaurant), their frequencies will be 2 times higher than others
        category_merchant_number = ceil(city_merchant_number/(len(category_list)+ 2 * len(brick_and_mortar))) 

        for c in category_list:
            merchant_number = category_merchant_number
            if c in brick_and_mortar:
                merchant_number = 3 * category_merchant_number
            for _ in range(merchant_number):
                merchant_fraud_flag = random.randint(1,100) 
                # If hit: 1% chance; 5% percent chance and the category is of moderate risk; 10% percent chance and the category is of high risk, then this merchant is compromised.
                if merchant_fraud_flag == 1 or (merchant_fraud_flag <= 5 and c in moderate_risk_cates) or (merchant_fraud_flag <= 10 and c in high_risk_cates):
                    fraud_risk = 1
                else:
                    fraud_risk = 0
                print(f"{c}|{fake.company()}|{'|'.join(randomize_coordinate(*freq_n_coordinates[city][1],0.5))}|{fraud_risk}")
    
    # restore original sdtout when done
    if cust_merchants_path is not None:
        sys.stdout = original_sys_stdout
        