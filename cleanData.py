import sqlite3

DB_PATH = "prototype.db"

def show_dirty_data(conn):
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT account_id, raw_account_name FROM accounts"
    ).fetchall()
    print("Sample dirty account names:")
    for row in rows:
        print(f"    {row[0]}    |   {row[1]}")


def clean_accounts(conn):
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT account_id, raw_account_name FROM accounts").fetchall()

    for row in rows:
        account_id = row[0]
        raw_name = row[1]

        if raw_name is None:
            clean_name = "Unknown"
        else:
            clean_name = raw_name.strip().title()

        cur.execute(
            "UPDATE accounts SET account_name = ? WHERE account_id = ?", (clean_name, account_id))

    

def clean_brokers(conn):
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT broker_id, producer_state, relationship_owner FROM brokers").fetchall()

    for row in rows:
        broker_id = row[0]
        raw_state = row[1]
        raw_relationship_owner = row[2]

        if raw_state is None:
            clean_state = "Unknown"
        else: 
            clean_state = raw_state.upper().strip()   

        if raw_relationship_owner is None:
            clean_relationship_owner = "Unknown"
        else:
            clean_relationship_owner = raw_relationship_owner.strip().title()

        cur.execute(
            "UPDATE brokers SET producer_state = ?, relationship_owner = ? WHERE broker_id = ?", (clean_state, clean_relationship_owner, broker_id))



def main():
    conn = sqlite3.connect(DB_PATH)
    show_dirty_data(conn)
    clean_accounts(conn)
    clean_brokers(conn)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()