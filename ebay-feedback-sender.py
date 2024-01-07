import calendar
import locale
from datetime import datetime
from ebaysdk.trading import Connection
from pprint import pprint
import os
import argparse
from dotenv import load_dotenv

# Get the current month
current_month = datetime.now().month

# Calculate the default month as the last month before the current month
default_month = current_month - 1 if current_month > 1 else 12

# Initialize argument parser
parser = argparse.ArgumentParser(
    description="Send messages to eBay buyers with the option to select the language or skip feedback for certain names.")

# Add an option to select the language
parser.add_argument('--language', choices=['english', 'italian'], default='english',
                    help="Select the language for the messages (default: english)")

# Add an option to specify names to skip
parser.add_argument('--skip-names', nargs='+', default=[],
                    help="Comma or space-separated list of names to skip when sending feedback")

# Add an option to set a custom month for searches
parser.add_argument('--custom-month', type=int, default=default_month, choices=range(1, 13),
                    help="Set a custom month for searches (1-12)")

# Parse command line arguments
args = parser.parse_args()

# Convert the list of names to skip to a set for efficient lookup
names_to_skip = set(args.skip_names)

# Calculate the start and end dates based on the custom month
if args.custom_month:
    current_date = datetime.now()
    custom_month = args.custom_month

    # Calculate the number of days in the selected month
    last_day_of_month = calendar.monthrange(current_date.year, custom_month)[1]

    # Set the start date as the first day of the selected month
    start_date = datetime(current_date.year, custom_month, 1)

    # Set the end date as the last day of the selected month
    end_date = datetime(current_date.year, custom_month, last_day_of_month)

    # Adjust the year if the selected month is December
    if custom_month == 12:
        start_date = start_date.replace(year=current_date.year - 1)
        end_date = end_date.replace(year=current_date.year - 1)

# Determine the language based on the selected option
if args.language == 'english':
    message_body = "Hello, I noticed that you haven't left feedback for your recent purchase. We value your feedback and would appreciate it if you could share your experience with us. If you have any questions or concerns, please feel free to reach out to us. Thank you, BMS!"
    subject = "Feedback Request from eBay Seller BeppeMokikaShop"
    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
elif args.language == 'italian':
    message_body = "Ciao, ho notato che non hai ancora lasciato un feedback per il tuo acquisto recente. Valutiamo molto il tuo feedback e saremmo grati se volessi condividere la tua esperienza con noi. Se hai domande o dubbi, non esitare a contattarci. Grazie, BMS!"
    subject = "Richiesta di Feedback da parte del Venditore eBay BeppeMokikaShop"
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')
# Now you have the variables `message_body` and `subject` set in the desired language.

# Load environment variables from .env file
load_dotenv()

# Read names to skip from a file
with open('skip_names.txt', 'r') as file:
    names_to_skip = set(file.read().splitlines())

# Format the dates in a format compatible with eBay requests
start_date_str = start_date.strftime('%Y-%m-%dT00:00:00.000Z')
end_date_str = end_date.strftime('%Y-%m-%dT23:59:59.999Z')

# Set connection parameters for the eBay Trading API
api = Connection(
    domain='api.ebay.com',
    appid=os.environ.get('EBAY_APP_ID'),
    devid=os.environ.get('EBAY_DEV_ID'),
    certid=os.environ.get('EBAY_CERT_ID'),
    token=os.environ.get('EBAY_TOKEN'),
    config_file=None
)

# Set filters for the search
filters = {
    'DetailLevel': 'ReturnAll',
    'CreateTimeFrom': start_date_str,
    'CreateTimeTo': end_date_str,
    'Pagination': {
        'EntriesPerPage': '100',  # Maximum number of orders per page
        'PageNumber': '1'  # Page number
    },
}

# Perform a search for completed orders
response = api.execute('GetOrders', filters)

# Extract completed orders
completed_orders = response.dict()['OrderArray']['Order']

# Calculate the selected month and year
selected_month_name = start_date.strftime('%B')
selected_year = start_date.year


# Add the month and year to the "Number of orders found" message
print(
    f"Number of orders found in {selected_month_name} {selected_year}: {len(completed_orders)}")

# Initialize a variable to keep track of the total feedback count
total_feedback_count = 0

# Initialize a list to store users when there's no FeedbackDetailArray
users_without_feedback = []

# Iterate through completed orders and check feedback for each item
for order in completed_orders:
    buyer_user_id = order['BuyerUserID']
    order_creation_time = order['CreatedTime']  # Data di creazione dell'ordine
    order_creation_date = datetime.strptime(
        order_creation_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    date_and_time = order_creation_date.strftime('%d %B %Y %H:%M:%S')

    # Check if the buyer's name is in the set of names to skip
    if buyer_user_id in names_to_skip:
        print(
            f"Skipping feedback for {buyer_user_id} (name is in the skip list)")
        continue

    # Check if there are multiple transactions in the order
    if isinstance(order['TransactionArray']['Transaction'], list):
        transactions = order['TransactionArray']['Transaction']
    else:
        transactions = [order['TransactionArray']['Transaction']]

    for transaction in transactions:
        item_id = transaction['Item']['ItemID']
        item_title = transaction['Item']['Title']  # Nome dell'inserzione

        # Create filters for GetFeedback request
        feedback_filters = {
            'DetailLevel': 'ReturnAll',
            'ItemID': item_id,
            'FeedbackType': 'FeedbackReceived',
        }

        # Execute GetFeedback request
        feedback_response = api.execute('GetFeedback', feedback_filters)
        feedback_info = feedback_response.dict()

        # Check if there is no feedback for this item
        if 'FeedbackDetailArray' not in feedback_info:
            users_without_feedback.append(buyer_user_id)

            # Create a request to send the message
            message_request = {
                'ItemID': item_id,
                'MemberMessage': {
                    'ItemID': item_id,
                    'QuestionType': 'General',
                    'RecipientID': buyer_user_id,
                    'Body': message_body,
                    'Subject': subject,
                }
            }

            # Execute the request to send the message
            response = api.execute(
                'AddMemberMessageAAQToPartner', message_request)

            # Check the response to verify if the message was sent successfully
            if response.reply.Ack == 'Success':
                print(
                    f"Message sent successfully to {buyer_user_id} for Item ID {item_id} {item_title} on {date_and_time}")
            else:
                print(
                    f"There was an error sending the message to {buyer_user_id} for Item ID {item_id} {item_title} on {date_and_time}")
