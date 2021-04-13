# Get your token at https://admin.typeform.com/account#/section/tokens
TYPEFORM_API_TOKEN = "<Your Typeform API token>"

# Form ID may be found in form URL: https://admin.typeform.com/form/<Form ID>/create
FORM_ID = "<Typeform form ID>"

# Name or path to SQLite DB file. File will be created if absent and cleaned up if present
DB_FILE_NAME = "<Name or path to DB file>"


# Advanced settings. Change only if you know what you are doing

# Amount of responses that will be retrieved per one request to Typeform API
# Maximum - 1000
RESPONSES_PAGE_SIZE = 100

# Name of table that holds fields metadata 
TABLE_NAME_FIELDS = "fields"

# Name of table that holds responses and single-choice answers
TABLE_NAME_RESPONSES = "responses"

# If set to True, one table per one multiselect answer will be created
# If False - all multiselect answers will be in one table
SEPARATE_TABLES_FOR_MULTISELECT = True

# Prefix for each multiselect answer table if SEPARATE_TABLES_FOR_MULTISELECT = True
TABLE_PREFIX_MULTISELECT = ""

# Name for common multiselect answer table if SEPARATE_TABLES_FOR_MULTISELECT = False
TABLE_NAME_MULTISELECT = "multiselect"
