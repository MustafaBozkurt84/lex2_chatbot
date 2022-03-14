import json
import datetime
import time
import os
import dateutil.parser
import logging
import datetime
import random


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }



def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
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
def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


# --- Helper Functions ---


def name_number(name):
    """
    These function will check that name involves any number
    """
    list_of_numbers = []
    for i in list(str(name)):
        try:
            i = int(i)
            list_of_numbers.append(i)
        except:
            pass
    if len(list_of_numbers) > 0:
        return False
    else:
        return True


def customer_number_digits(customernumber):
    """
    Will check if the customer number consists of 4 digits
    """

    try:
        int(customernumber)
        if len(list(customernumber)) == 4:
            return True
    except ValueError:
        return False


def convert_date_to_month(date):
    try:
        datem = datetime.datetime.strptime(date, "%Y-%m-%d")
        return datem.month
    except ValueError:
        pass


def get_day_difference(later_date, earlier_date):
    later_datetime = dateutil.parser.parse(later_date).date()
    earlier_datetime = dateutil.parser.parse(earlier_date).date()
    return abs(later_datetime - earlier_datetime).days


def generate_invoice_price():
    return random.randrange(50, 150)


def convert_month_date(date):
    months = ['january', 'february', 'march', 'april',
              'may', 'june', 'july', 'august',
              'september', 'october', 'november', 'december']

    month = months[int(convert_date_to_month(date)) - 1]
    return month
def isvalid_name(name):
    return name_number(name)


def isvalid_customernumber(customernumber):
    return customer_number_digits(customernumber)


def isvalid_date(date):
    months = ['january', 'february', 'march', 'april',
              'may', 'june', 'july', 'august',
              'september', 'october', 'november', 'december']

    month = months[int(convert_date_to_month(date)) - 1]
    return month.lower() in months


def isvalid_birthday(birthday):
    try:
        later_date = str(datetime.datetime.today()).split()[0]
        earlier_date = birthday
        day_diff = get_day_difference(later_date, earlier_date)
        if (day_diff > 6570):
            if (day_diff < 40000):
                return True
            else:
                return False
        else:
            return False
    except ValueError:
        return False


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_invoice(slots):
    name = try_ex(lambda: slots['name'])
    customernumber = try_ex(lambda: slots['customernumber'])
    date = try_ex(lambda: slots['date'])
    birthday = try_ex(lambda: slots['birthday'])

    if name and not isvalid_name(name):
        return build_validation_result(
            False,
            'name',
            'I am not sure {} is your name. Would you like me to get your information again?'.format(name)
        )

    if customernumber:
        if not isvalid_customernumber(customernumber):
            return build_validation_result(False, 'customernumber',
                                           'Your customer number must be 4 digits.  Please re-enter your customer number?')

    if date and not isvalid_date(date):
        return build_validation_result(
            False,
            'date',
            'Please say again which month you want to receive the invoice for?'
        )
    if birthday and not isvalid_birthday(birthday):
        return build_validation_result(
            False,
            'birthday',
            'The date you entered is not a logical date or you are under 18 years old, please re-enter the date of birth?'
        )

    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """


def invoice_intent(intent_request):
    """
    Performs dialog management and fulfillment for invoice .

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    name = try_ex(lambda: intent_request['currentIntent']['slots']['name'])
    customernumber = try_ex(lambda: intent_request['currentIntent']['slots']['customernumber'])
    date = try_ex(lambda: intent_request['currentIntent']['slots']['date'])

    birthday = try_ex(lambda: intent_request['currentIntent']['slots']['birthday'])
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'invoice',
        'name': name,
        'customernumber': customernumber,
        'date': date,
        'birthday': birthday
    })

    session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_invoice(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price
        # back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.
        if name and customernumber and date and birthday:
            # The price of the hotel has yet to be confirmed.
            price = generate_invoice_price()
            session_attributes['currentInvoicePrice'] = price
        else:
            try_ex(lambda: session_attributes.pop('currentInvoicePrice'))
        reservation = json.dumps({
        'ReservationType': 'invoice',
        'name': name,
        'customernumber': customernumber,
        'date': convert_month_date(date),
        'birthday': birthday
    })
        session_attributes['currentReservation'] = reservation
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # In a real application, this would likely involve a call to a backend service.
    logger.debug('invoice under={}'.format(reservation))

    try_ex(lambda: session_attributes.pop('currentInvoicePrice'))
    try_ex(lambda: session_attributes.pop('currentReservation'))
    session_attributes['lastConfirmedReservation'] = reservation

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, Your transaction has been completed successfully.   Please let me know if you need ant other help '

        }
    )



# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'invoice':
        return invoice_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
