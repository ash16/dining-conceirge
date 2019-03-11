import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            'isValid': is_valid,
            'violatedSlot': violated_slot
        }
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
        
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message,
        }
    }

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def get_dining_suggestions(slots):
    header = {
        'authorization':"BEARER <API-KEY>",
        'cache-control' : "no-cache", 
        }
    params = {'location':slots['Location'], 'category':'restaurant,'+slots['Cuisine'], 'limit':3}
    
    res = requests.get("https://api.yelp.com/v3/businesses/search", params = params, headers = header)
    return res.text
    
    

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    print("USE ME :", event)
    return dispatch(event)

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    # logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningBookingIntent':
        #If correct intent name validate. 
        return diningSuggestionsValidate(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')

def validate_book_dining(diningDate, diningTime, numberOfPeople, cuisine, location):
    cuisine_types = ['indian', 'italian', 'japanese', 'spanish', 'lebanese', 'mexican', 'continental', 'chinese', 'vietnamese','thai','indonesian','ethiopian'];
    location_types = ['manhattan', 'venice', 'paris', 'mumbai', 'delhi', 'kyoto', 'tokyo', 'xian', 'shanghai', 'beijing', 'new york', 'bengaluru'];

    # return build_validation_result(True, '')
    if cuisine is not None and (cuisine not in cuisine_types):
        return build_validation_result(False, 'Cuisine', 'We don\'t offer the cuisine you requested. Please pick something else.');
    
    if numberOfPeople is not None and (parse_int(numberOfPeople) < 0 or parse_int(numberOfPeople) > 15):
        return build_validation_result(False, 'NumberOfPeople', 'We can only seat between [1,15] people.')
        
    if location is not None and (location not in location_types):
        return build_validation_result(False, 'Location', 'We don\'t offer service in the location. Please pick a different location.')
    
    if diningTime is not None: 
        if len(diningTime) != 5:
            return build_validation_result(False, 'DiningTime', 'Sorry, I did not recognize that, please enter time!')

        hour, minute = diningTime.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'DiningTime', 'Sorry, I did not recognize that, what time would you like your reservations for?')
        
        if hour < 0 or hour > 24:
            return buildValidationResult(False, 'DiningTime', 'Pick a time between 0 and 24 hours!')

    if diningDate is not None:
        if not isvalid_date(diningDate):
            return build_validation_result(False, 'DiningDate', 'Invalid Dining date selected! Please enter correct details.')
            
        if datetime.datetime.strptime(diningDate, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'DiningDate', 'Dining date must be after today\'s date.')

    return build_validation_result(True, None, None)

def diningSuggestionsValidate(intent_request):
    
    dining_date = intent_request['currentIntent']['slots']['DinnerDate']
    dining_time = intent_request['currentIntent']['slots']['DinnerTime']
    no_of_people = intent_request['currentIntent']['slots']['NumberOfPeople']
    cuisine = intent_request['currentIntent']['slots']['Cuisine']
    location = intent_request['currentIntent']['slots']['Location']
    
    source = intent_request['invocationSource']
    
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    if source == 'DialogCodeHook':
        slots = intent_request['currentIntent']['slots']
        validation_result = validate_book_dining(dining_date, dining_time, no_of_people, cuisine, location)
        
        if validation_result['isValid'] is False:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(output_session_attributes, intent_request['currentIntent']['name'], slots, validation_result['violatedSlot'], validation_result['message'])
        
        return delegate(output_session_attributes, slots)
        
    if source == 'FulfillmentCodeHook':
        slots = intent_request['currentIntent']['slots']
        result = get_dining_suggestions(slots)
        return close(
            output_session_attributes,
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': result
            })

        
    return close(
        output_session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Okay, I have made your meal reservations!'
        }
    )