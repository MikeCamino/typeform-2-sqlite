from typeform import Typeform
import sqlite3
import settings

# Returns column definition based on typeform field type
def field_to_column_def(field):
    mapping = {
        "matrix" : "", # I don't know what type it is
        "ranking" : " INT",
        "date" : " DATETIME",
        "dropdown" : " VARCHAR",
        "email" : " VARCHAR",
        "file_upload" : " VARCHAR",
        "group" : "", # should not be created in DB
        "legal" : " INT",
        "long_text" : " VARCHAR",
        "multiple_choice" : " VARCHAR", # for multiple choice fields without multiselect
        "number" : " INT",
        "opinion_scale" : " VARCHAR",
        "payment" : " VARCHAR",
        "picture_choice" : " VARCHAR",
        "rating" : " INT",
        "short_text" : " VARCHAR",
        "statement" : "", # should not be created in DB
        "website" : " VARCHAR",
        "yes_no" : " BOOLEAN",
        "phone_number" : " VARCHAR",
    }

    return f"'{field['ref'].replace('-', '_')}' {mapping[field['type']]}"


# constants and advanced settings
TABLE_FIELDS = "fields"
TABLE_RESPONSES = "responses"
TABLE_MULTISELECT = "multiselect"
RESPONSES_PAGE_SIZE = 1000 # 1000 - is maximum that Typeform allows

tf = Typeform(settings.TYPEFORM_API_TOKEN)

con = sqlite3.connect(settings.DB_FILE_NAME)
cur = con.cursor()

form = tf.forms.get(settings.FORM_ID)

print(f"Form \"{form['title']}\" ({form['id']}) retireved successfully")

# Clean up DB
cur.execute(f"drop table if exists {TABLE_FIELDS}")
cur.execute(f"drop table if exists {TABLE_MULTISELECT}")
cur.execute(f"drop table if exists {TABLE_RESPONSES}")

# Create tables
# Fields metadata
cur.execute(f"create table if not exists {TABLE_FIELDS} (id VARCHAR, title TEXT, ref VARCHAR, type VARCHAR, allow_multiple BOOLEAN)")
# Multiselect responses
cur.execute(f"create table if not exists {TABLE_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer)")

fields = [] # All fields except multiselect, group and statement
multichoice_field_names = []

for f in form['fields']:
    allow_multiple_selection = False
    if f['type'] == 'multiple_choice' and f['properties']['allow_multiple_selection']:
        multichoice_field_names.append(f["ref"])
        allow_multiple_selection = True
    elif f["type"] == "group" or f["type"] == "statement":
        continue
    else:
        fields.append(f)
    
    cur.execute("insert into fields values (?,?,?,?,?)", (f['id'], f['title'], f['ref'], f['type'], allow_multiple_selection))

con.commit()

print("Fields and multiselect tables created successfully")

# Create responses table
col_names = ",".join(field_to_column_def(x) for x in fields)
responses_query = f"create table if not exists {TABLE_RESPONSES} (id VARCHAR, landed_at DATETIME, submitted_at DATETIME, {col_names})"
cur.execute(responses_query)

print("Responses table created successfully")

# Get form responses
responses = tf.responses.list(settings.FORM_ID, RESPONSES_PAGE_SIZE)

print(f"Retrieved {len(responses['items'])} results of {responses['total_items']}")

answers_written = 0
multichoice_answers_written = 0

for r in responses["items"]:
    answers = {}
    multichoice_answers = {}

    # Common answer fields
    answers["id"] = r["response_id"]
    answers["landed_at"] = r["landed_at"]
    answers["submitted_at"] = r["submitted_at"]

    for a in r["answers"]:
        ref = a["field"]["ref"]
        if ref in multichoice_field_names:
            # Named options
            if a["choices"].get("labels", False):
                for i in range(len(a["choices"]["labels"])):
                    id = a["choices"]["ids"][i]
                    label = a["choices"]["labels"][i]
                    cur.execute(f"insert into {TABLE_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer) values (?,?,?,?,?)", (answers["id"], a["field"]["id"], ref, id, label))
                    multichoice_answers_written += 1
            # 'other' option
            if a["choices"].get("other", False):
                cur.execute(f"insert into {TABLE_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer) values (?,?,?,?,?)", (answers["id"], a["field"]["id"], ref, "other", a["choices"]["other"]))
                multichoice_answers_written += 1
        else:
            if a["type"] == "choice":
                if a["choice"]["id"] == "other":
                    answers[ref] = a["choice"]["other"]
                else:
                    answers[ref] = a["choice"]["label"]
            else:
                answers[ref] = a[a["type"]]
    
    # writing single choice answers to table
    answer_columns = "','".join(x.replace("-", "_") for x in answers)
    answer_insert = f"insert into {TABLE_RESPONSES} ('{answer_columns}') values ({','.join(['?'] * len(answers))})"
    cur.execute(answer_insert, tuple(answers.values()))
    answers_written += 1

con.commit()

print(f"{answers_written} answers and {multichoice_answers_written} multichoice answers written to DB")

con.close()

print(f"Export finished succesfully to {settings.DB_FILE_NAME}")
