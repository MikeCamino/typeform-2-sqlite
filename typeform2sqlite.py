from typeform import Typeform
import sqlite3
import settings
import os

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


tf = Typeform(settings.TYPEFORM_API_TOKEN)

if os.path.exists(settings.DB_FILE_NAME):
    os.remove(settings.DB_FILE_NAME)
con = sqlite3.connect(settings.DB_FILE_NAME)
cur = con.cursor()

form = tf.forms.get(settings.FORM_ID)

print(f"Form \"{form['title']}\" ({form['id']}) retireved successfully")

# Create fields metadata table
cur.execute(f"create table if not exists {settings.TABLE_NAME_FIELDS} (id VARCHAR, title TEXT, ref VARCHAR, type VARCHAR, allow_multiple BOOLEAN)")
print(f"'{settings.TABLE_NAME_FIELDS}' table created successfully")

fields = [] # All fields except multiselect, group and statement
multichoice_field_names = []

def add_field_to_metadata_table(field):
    if field['type'] == 'multiple_choice' and field['properties']['allow_multiple_selection']:
        multichoice_field_names.append(field["ref"])
        allow_multiple_selection = True
    else:
        fields.append(field)
        allow_multiple_selection = False

    cur.execute("insert into fields values (?,?,?,?,?)", (field['id'], field['title'], field['ref'], field['type'], allow_multiple_selection))

def process_fields(fields):
    for f in fields:
        if f["type"] == "group":
            # group fields contains other fields inside
            process_fields(f["properties"]["fields"])
            continue
        elif f["type"] == "statement":
            continue

        add_field_to_metadata_table(f)

process_fields(form["fields"])

if settings.SEPARATE_TABLES_FOR_MULTISELECT:
    # Multiselect responses in separate tables
    for mf in multichoice_field_names:
        cur.execute(f"create table if not exists '{settings.TABLE_PREFIX_MULTISELECT}{mf.replace('-','_')}' (response_id, answer_id, answer)")
        print(f"Multiselect field '{settings.TABLE_PREFIX_MULTISELECT}{mf.replace('-','_')}' table created successfully")
else:
    # Multiselect responses in single table
    cur.execute(f"create table if not exists {settings.TABLE_NAME_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer)")
    print(f"'{settings.TABLE_NAME_MULTISELECT}' table created successfully")

con.commit()

# Create responses table
col_names = ",".join(field_to_column_def(x) for x in fields)
responses_query = f"create table if not exists {settings.TABLE_NAME_RESPONSES} (id VARCHAR, landed_at DATETIME, submitted_at DATETIME, {col_names})"
cur.execute(responses_query)

print(f"'{settings.TABLE_NAME_RESPONSES}' table created successfully")

answers_written = 0
multichoice_answers_written = 0
last_response_token = None

# Get form responses
while True:
    responses = tf.responses.list(settings.FORM_ID, settings.RESPONSES_PAGE_SIZE, before=last_response_token)

    print(f"Retrieved {len(responses['items'])} results of remaining {responses['total_items']}")

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

                        if settings.SEPARATE_TABLES_FOR_MULTISELECT:
                            cur.execute(f"insert into '{settings.TABLE_PREFIX_MULTISELECT}{ref.replace('-','_')}' (response_id, answer_id, answer) values (?,?,?)", (answers["id"], id, label))
                        else:
                            cur.execute(f"insert into {settings.TABLE_NAME_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer) values (?,?,?,?,?)", (answers["id"], a["field"]["id"], ref, id, label))
                        multichoice_answers_written += 1
                # 'other' option
                if a["choices"].get("other", False):
                    if settings.SEPARATE_TABLES_FOR_MULTISELECT:
                        cur.execute(f"insert into '{settings.TABLE_PREFIX_MULTISELECT}{ref.replace('-','_')}' (response_id, answer_id, answer) values (?,?,?)", (answers["id"], "other", a["choices"]["other"]))
                    else:
                        cur.execute(f"insert into {settings.TABLE_NAME_MULTISELECT} (response_id, field_id, field_ref, answer_id, answer) values (?,?,?,?,?)", (answers["id"], a["field"]["id"], ref, "other", a["choices"]["other"]))
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
        answer_insert = f"insert into {settings.TABLE_NAME_RESPONSES} ('{answer_columns}') values ({','.join(['?'] * len(answers))})"
        cur.execute(answer_insert, tuple(answers.values()))
        answers_written += 1

    con.commit()

    if len(responses["items"]) == 0 or len(responses["items"]) == responses['total_items']:
        print("All responses processed")
        break

    last_response_token = responses["items"][-1]["token"]

print(f"{answers_written} answers and {multichoice_answers_written} multichoice answers written to DB")

con.close()

print(f"Export finished succesfully to {settings.DB_FILE_NAME}")
