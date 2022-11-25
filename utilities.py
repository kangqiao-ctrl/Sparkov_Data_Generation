from datetime import datetime
import math, random, argparse

def valid_date(s):
    try:
        return datetime.strptime(s, "%m-%d-%Y")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

def randomize_coordinate(lat, long, radius):
    # Randomize coordinate for the customers
    lat = float(lat)
    long = float(long)
    attraction = 3  # play with this value (density, https://stackoverflow.com/questions/66829191/how-to-generate-random-points-within-a-circular-area-with-higher-density-near-t)
    t = random.random() * 2 * math.pi
    r = random.random() ** attraction * radius  
    new_lat = lat + r * math.sin(t)
    new_long = long + r * math.cos(t)

    return str(new_lat), str(new_long)
    