from   datetime import timedelta, time, datetime
import numpy  as np
import pandas as pd
import json
import googlemaps
import os
import sys
import getopt

################################################################################
################################### FUNCTIONS ##################################
################################################################################

# setting up googlemaps API
GMAPS_API_KEY = 'AIzaSyBhBpQs5eoSsG-NvX2yKkFDGsDR8glhG0Y'
gmaps         = googlemaps.Client(key=GMAPS_API_KEY)

def set_to_midnight(dt):
    midnight = time(0)
    return datetime.combine(dt.date(), midnight)

def check_subdir(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

def extract_city_and_state(address):
    city, state = address.split(',')[0], (address.split(',')[1]).split(' ')[1]
    return city, state

def get_direction_from_zipcode(zipcode):
    '''
        Given a zip code, returns city and state from that location within United
        States. Exception if address cannot be found.
    '''
    address = str(zipcode) + ', United States'
    try:
        result    = gmaps.geocode(address)
        formatted_address = result[0]['formatted_address']
        return extract_city_and_state(formatted_address)
    except Exception as e:
        raise e

secondary = ['LTLV', 'LTLS']

def strip_date(date):
    return date.split(' ')[0]

def check_zipcode(zipcode):
    if len(str(zipcode)) == 5:
        return zipcode
    else:
        return None

def is_primary(trailer_type):
    return not trailer_type in secondary


################################################################################
################################### PARSER  ####################################
################################################################################

def parse_file():
    # opening file
    data = pd.read_excel('receiveremail/fedex_17-05-2018-3.xls')

    print("Raw Data elements (1): ", data.shape[0])

    print('Removing non available zip codes')
    data['Origin Zip']      = data['Origin Zip'].apply(check_zipcode)
    data['Destination Zip'] = data['Destination Zip'].apply(check_zipcode)
    data = data[pd.notnull(data['Origin Zip'])]
    data = data[pd.notnull(data['Destination Zip'])]

    print('Droping duplicates')
    data = data.drop_duplicates('Shipment ID')
    print("Raw Data elements (2): ", data.shape[0])

    print('Converting time formats')
    data['Pickup Cutoff Time']   = data['Pickup Cutoff Time'].apply(strip_date)
    data['Delivery Cutoff Time'] = data['Delivery Cutoff Time'].apply(strip_date)
    data['Pickup Cutoff Time']   = pd.to_datetime(data['Pickup Cutoff Time'],   format = '%m/%d/%Y')
    data['Delivery Cutoff Time'] = pd.to_datetime(data['Delivery Cutoff Time'], format = '%m/%d/%Y')

    print('Filling Missing Prices')
    data['Carrier Pay']          = data['Carrier Pay'].fillna(value=0)

    print('Processing')
    new_data_content = []
    for i in range(data.shape[0]):
        try:
            line = {}
            origin_city, origin_state           = get_direction_from_zipcode(data.iloc[i]['Origin Zip'])
            destination_city, destination_state = get_direction_from_zipcode(data.iloc[i]['Destination Zip'])
            line['origin']      = origin_city + ' ' + origin_state
            line['destination'] = destination_city + ' ' + destination_state
            line['clientid']    = data.iloc[i]['Commodity']
            line['contact']     = ''
            line['owner']       = 'fedex'
            line['demand']      = float(data.iloc[i]['Total Weight'])/1750
            line['est_demand']  = float(data.iloc[i]['Total Weight'])/1750
            line['load']        = float(data.iloc[i]['Total Weight'])
            line['est_load']    = float(data.iloc[i]['Total Weight'])
            line['cargotype']   = 'General Cargo'
            line['tripid']      = 'FX' + str(data.iloc[i]['Shipment ID'])
            line['ready']       = (set_to_midnight(datetime.today()) + timedelta(hours=8)).isoformat()
            line['pickupby']    = data.iloc[i]['Pickup Cutoff Time'].isoformat()
            line['dropready']   = data.iloc[i]['Delivery Cutoff Time'].isoformat()
            line['deliverby']   = data.iloc[i]['Delivery Cutoff Time'].isoformat()
            line['entered']     = datetime.today().isoformat()
            line['generated']   = 1
            line['primary']     = is_primary(data.iloc[i]['Trailer Type'])
            line['secondary']   = not(is_primary(data.iloc[i]['Trailer Type']))
            line['price']       = float(data.iloc[i]['Carrier Pay'])
            line['est_price']   = float(data.iloc[i]['Carrier Pay'])
            line['vehicletype'] = '53'
            line['cost']        = 0
            line['miles']       = 0
            line['trucks']      = []
            line['matchid']     = None
            line['cost']        = 0
            line['miles']       = 0
            line['specinfo']    = ''
            line['equipment']   = ''
            line['arrival']     = 0
            line['departure']   = 0
            line['rpm']         = 0
            line['emptymiles']  = 0
            new_data_content.append(line)
        except Exception as e:
            print(e)

    json_results = json.dumps(new_data_content, indent=4)
    return json_results