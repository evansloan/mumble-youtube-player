import sqlite3

conn = sqlite3.connect('users.db', check_same_thread=False)


def create_db_tables():
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS ignored (username text)')
    c.execute('CREATE TABLE IF NOT EXISTS mods (username text)')
    conn.commit()


if __name__ == '__main__':
    create_db_tables()
