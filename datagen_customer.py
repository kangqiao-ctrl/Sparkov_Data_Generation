from faker import Faker
import sys, math
from datetime import date
import random
from main_config import MainConfig
import argparse
import pathlib
from bisect import bisect_left


headers = [
    'ssn',
    'cc_num',
    'first',
    'last',
    'gender',
    'street',
    'city',
    'state', 
    'zip', 
    'lat', 
    'long', 
    'city_pop',
    'job', 
    'dob', 
    'acct_num', 
    'profile'
]


def make_cities():
    cities = {}
    with open('./demographic_data/locations_partitions.csv', 'r') as f:
        for line in f.readlines()[1:]:
            cdf, output = line.strip().split(',')
            cities[float(cdf)] = output.split('|')
        return cities


def make_age_gender_dict():
    gender_age = {}
    prev = 0
    with open('./demographic_data/age_gender_demographics.csv', 'r') as f:
        for line in f.readlines()[1:]:
            l = line.strip().split(',')
            prev += float(l[3])
            gender_age[prev] = (l[2], float(l[1]))
        return gender_age


def randomize_coordinate(lat, long, radius):
    # Randomize coordinate for the customers
    lat = float(lat)
    long = float(long)
    attraction = 3  # play with this value (density, https://stackoverflow.com/questions/66829191/how-to-generate-random-points-within-a-circular-area-with-higher-density-near-t)
    t = random.random() * 2 * math.pi
    r = random.random() ** attraction * radius  
    new_lat = lat + r * math.cos(t)
    new_long = long + r * math.sin(t)

    return str(new_lat), str(new_long)


class Customer:
    # Randomly generates all the attributes for a customer

    def __init__(self, config, seed_num=None):
        self.fake = Faker()
        if seed_num is not None:
            Faker.seed(seed_num)
        # turn all profiles into dicts to work with
        self.all_profiles = MainConfig(config).config # KQ: main_config.json 


    def generate_customer(self):
        self.gender, self.dob, self.age = self.generate_age_gender()
        self.addy = self.get_random_location()

        city_pos = self.addy # Save the generated location for later use

        self.addy[3], self.addy[4] = randomize_coordinate(self.addy[3], self.addy[4], 0.5) # 'Shake' the customers' coordinates

        customer_data = [
            self.fake.ssn(),
            self.fake.credit_card_number(),
            self.get_first_name(),
            self.fake.last_name(),
            self.gender,
            self.fake.street_address()
        ] + self.addy + [
            self.fake.job(),
            self.dob,
            str(self.fake.random_number(digits=12)),
            self.find_profile()
        ]


        return customer_data, city_pos # Also return newly generated customer coordinates

    def get_first_name(self):
        if self.gender == 'M':
            return self.fake.first_name_male()
        else:
            return self.fake.first_name_female()

    def generate_age_gender(self):
        n = random.random()
        g_a = age_gender[min([a for a in age_gender if a > n])]

        while True:
            age = int(g_a[1])
            today = date.today()
            try:
                rand_date = self.fake.date_time_this_century()
                # find birthyear, which is today's year - age - 1 if today's month,day is smaller than dob month,day
                birth_year = today.year - age - ((today.month, today.day) < (rand_date.month, rand_date.day))
                dob = rand_date.replace(year=birth_year)

                # return first letter of gender, dob and age
                return g_a[0][0], dob.strftime("%Y-%m-%d"), age
            except:
                pass

    # find nearest city
    def get_random_location(self):
        """
        Assumes lst is sorted. Returns closest value to num.
        """
        num = random.random()
        lst = list(cities.keys())
        pos = bisect_left(lst, num)
        if pos == 0:
            return cities[lst[0]]
        if pos == len(cities):
            return cities[lst[-1]]
        before = lst[pos - 1]
        after = lst[pos]
        if after - num < num - before:
            return cities[after]
        else:
            return cities[before]

    def find_profile(self):
        city_pop = float(self.addy[-1])

        match = []
        for pro in self.all_profiles:
            # -1 represents infinity
            if (self.gender in self.all_profiles[pro]['gender']
                and self.age >= self.all_profiles[pro]['age'][0]
                and (self.age < self.all_profiles[pro]['age'][1] 
                    or self.all_profiles[pro]['age'][1] == -1) 
                and city_pop >= self.all_profiles[pro]['city_pop'][0] 
                and (city_pop < self.all_profiles[pro]['city_pop'][1] 
                    or self.all_profiles[pro]['city_pop'][1] == -1)
                ):
                match.append(pro)
        if match == []:
            match.append('leftovers.json')

        # found overlap -- write to log file but continue
        if len(match) > 1:
            with open('profile_overlap_warnings.log', 'a') as f:
                f.write(f"{' '.join(match)}: {self.gender} {str(self.age)} {str(city_pop)}\n")
        return match[0]


def main(num_cust, seed_num, config, out_path):
    if num_cust <= 0 or seed_num is None or config is None:
        parser.print_help()
        exit(1)

    # setup output to file by redirecting stdout (Should be put into utilities later)
    original_sys_stdout = sys.stdout
    if out_path is not None:
        f_out = open(out_path, 'w')
        sys.stdout = f_out

    # print headers
    print("|".join(headers))

    c = Customer(config=config, seed_num=seed_num)
    activated_city_pos = []

    for _ in range(num_cust):
        customer_data_pos = c.generate_customer() # Generate attributes for individual customers
        activated_city_pos.append(customer_data_pos[1]) # KQ: Get a customer coordinates list
        print("|".join(customer_data_pos[0]))

    # restore original sdtout when done
    if out_path is not None:
        sys.stdout = original_sys_stdout
    
    return activated_city_pos # Return the city coordinate list for generating merchants later

cities = make_cities()
age_gender = make_age_gender_dict()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Customer Generator')
    parser.add_argument('count', type=int, help='Number of customers to generate', default=10)
    parser.add_argument('seed', type=int, nargs='?', help='Random generator seed', default=42)
    parser.add_argument('config', type=pathlib.Path, nargs='?', help='Profile config file (typically profiles/main_config.json")', default='./profiles/main_config.json')
    parser.add_argument('-o', '--output', type=pathlib.Path, help='Output file path', default=None)

    args = parser.parse_args()
    num_cust = args.count
    seed_num = args.seed
    config = args.config
    out_path = args.output

    main(num_cust, seed_num, config, out_path)