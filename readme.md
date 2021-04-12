# Typeform-2-sqlite

Python script that turns your Typeform form responses into relational database.

# Why you may need it

Typeform is a great tool to gather people's opinions. But when it comes to processing results one problem appears: multiple selection answers.

While all other types of answer lies perfectly in two-dimensional table that may be processed in Excel or other spreadsheet app (pivot tables rules), each multi-selection answer generates a column for each option and there is no easy way to work with them in spreadsheet

Obvious solution here is to use the power of relational database.

# Why SQLite

SQLite is full-powered relational DB engine that works on every platform and requires barely nothing to run. Its databases are portable (one file per DB) and thus may be sent or stored anywhere you like.

SQLite supports all modern SQL features: memory tables, views, triggers, transactions, functions, extensions... even JSON queries (in most recent versions).

It is totally free and public domain. It works on all modern OS and doesn't require installation - download and run.

There are many ways to work with SQLite DB:

- Embedding SQLite into application
- Using ODBC or other drivers
- From command-line on any OS
- Using one of desktop applications. I use [SQLite Studio](https://sqlitestudio.pl/) but there are a lot of other options.
- Or just in browser: [https://sqliteonline.com/](https://sqliteonline.com/)

# How typeform-2-sqlite works

Very straightforward: script connects to Typeform API, gets your form data and creates SQLite DB with results and some metadata. Multi-select answers are stored in a separate table which allows you to use JOIN clauses.

## Tables

Typeform-2-sqlite creates 3 tables:

### fields

Reference for all questions in your form: its title, ref and some options

### responses

All responses except multi-select questions in a form of a flat table.

Question's `ref` is a name of a column (see below on how to set `ref`s for your questions)

### multiselect

All multi-select question answers

`response_id` - ID from `responses` table.

`field_id` - form field ID (just for reference, not human readable)

`field_ref` - form field `ref`.

`answer_id` - answer option ID. May be used to calculate number of unique answers for example (since answers themselves may be identical for different questions).

`answer` - answer data itself.

# Important things before you start

## Set field references

Typeform gives every question that you create an unique system ID called reference or `ref`

These refs are used in SQLite DB as column names and `field_ref` in `multiselect` table and will heavily be used by you to construct queries. But by default they are not human readable, like 02116c87-94e8-40c0-a09b-e8211ea1c5ce

Before you run script you **should** give these refs human readable names

To do that:

- In "classic" form builder:
    1. Click on question number to reveal properties panel on the left
    2. Look for "Question reference" option at the very bottom
    3. Give question a new name
- In "modern" form builder:
    1. Open form settings (gear icon on top of the left panel)
    2. Open "Block references" at the very bottom
    3. Give each question a new name and save

### Simple rules for field names

1. Names should only contain lowercase latin letters, numbers and underscrores (Typeform allows to use hyphens but SQLite doesn't like them and they will be replaced with undescrores by script)
2. Names shouldn't start with number (SQLite doesn't allow this in column names)
3. Names should be descriptive and short as possible. This is not a strict rule - just for your convenience

## Get API token

Typeform-2-sqlite needs access to your Typeform data to run. To allow this you will need API token.

1. From Typeform admin page open your account settings in top-right corner
2. Go to "Personal tokens" section
3. Click "Generate new token" at the top-right
4. Give your token a name. For example "typeform-2-sqlite". This way you will know how is this token used and will be able to recall it anytime you like
5. Set scopes. Typeform-2-sql needs only two: `Forms - Read` and `Responses - Read`
6. Click "Generate token"
7. Copy your token and store it somewhere. You will need it in next steps

# Installation and run

Typeform-2-sqlite needs Python 3 to run

## Clone or download script

### Clone

Open console and run

```bash
git clone https://github.com/MikeCamino/typeform-2-sqlite.git
```

### Download

- Download [https://github.com/MikeCamino/typeform-2-sql/archive/refs/heads/master.zip](https://github.com/MikeCamino/ArchStory/archive/refs/heads/master.zip)
- Unpack to a directory of your choice

## Install Python 3

Refer to official docs for your OS [https://www.python.org/downloads/](https://www.python.org/downloads/)

## Install dependencies

In your console run

```bash
pip install typeform
```

## Set API token and other settings

In `settings.py` set following options:

`TYPEFORM_API_TOKEN` - API token obtained on previous step

`FORM_ID` - ID of your form. May be found in URL when you edit your form `https://admin.typeform.com/form/<Form ID>/create`

`DB_FILE_NAME` - name of DB to be created

## Run

In console change to typeform-2-sqlite directory and run

```bash
python typeform2sqlite.py
```

## Open

Open DB with the weapon of your choice and start querying :)