# eBay Feedback Sender

The eBay Feedback Sender is a Python script that automates the process of sending feedback messages to eBay buyers for completed orders within a specified date range. The script provides options to customize the language of the message, skip feedback for specific buyers, and set custom date ranges.

## Installation
To use the eBay Feedback Sender, you need to have Python 3 installed on your system and some packages.
You can install these packages by running the following command in your terminal or command prompt:
```shell
pip install -r requirements.txt
```

## Usage
To use the eBay Feedback Sender, follow these steps:

You can run the program by navigating to the directory where the program is stored and running the following command:
```shell
python ebay-feedback-sender.py [--options]
```

Options:
- --language: Choose the language for the feedback message (default: english).
Available options: 'english', 'italian'
- --skip-names: Specify names to skip when sending feedback. Provide a list of names separated by commas or spaces
- --custom-month: Set a custom month for the search (1-12, default: last month)

The script will send feedback messages to buyers based on the specified options.

Please note that the program relies on environment variables for the Ebay Api. Make sure to set these variables in a .env file in the same directory as the script.

## Note
You can provide a list of buyers names to skip in the "skip_names.txt" file or through the command line if needed.
