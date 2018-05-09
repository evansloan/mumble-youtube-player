import sqlite3

conn = sqlite3.connect('../users.db', check_same_thread=False)


def create_db_tables():
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS ignored (username text)')
    c.execute('CREATE TABLE IF NOT EXISTS mods (username text)')


def is_mod(username):
    c = conn.cursor()
    if username in [x[0] for x in c.execute('SELECT * FROM mods')]:
        return True
    return False


def is_ignored(username):
    c = conn.cursor()
    if username in [x[0] for x in c.execute('SELECT * FROM ignored')]:
        return True
    return False


def remove_html_markup(s):
    tag = False
    quote = False
    out = ''

    for char in s:
        if char == '<' and not quote:
            tag = True
        elif char == '>' and not quote:
            tag = False
        elif (char == '"' or char == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + char
    return out
