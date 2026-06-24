CREATE TABLE IF NOT EXISTS lines_of_business (
    lob_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    raw_account_name TEXT,
    account_name TEXT,
    account_tier TEXT CHECK (account_tier IN ('Small', 'Medium', 'Large'))
);

CREATE TABLE IF NOT EXISTS brokers (
    broker_id TEXT PRIMARY KEY,
    producer_name TEXT NOT NULL,
    producer_state TEXT,
    relationship_owner TEXT
);


CREATE TABLE IF NOT EXISTS carriers (
    carrier_id TEXT PRIMARY KEY,
    carrier_name TEXT NOT NULL,
    underwriter TEXT   
);

CREATE TABLE IF NOT EXISTS submission_groups (
    submission_group_id TEXT PRIMARY KEY,
    submission_group_target_premium REAL,
    account_id TEXT REFERENCES accounts(account_id),
    broker_id TEXT REFERENCES brokers(broker_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    control_number TEXT PRIMARY KEY,
    account_id TEXT REFERENCES accounts(account_id),
    broker_id TEXT REFERENCES brokers(broker_id),
    lob_name TEXT REFERENCES lines_of_business(lob_name),
    effective_date TEXT NOT NULL, /*DATE*/
    expiration_date TEXT NOT NULL,  /*DATE*/
    target_premium REAL,  /*NUMERIC(10,2) in SQL Server*/
    priority TEXT,
    type TEXT NOT NULL,
    submission_group_id TEXT REFERENCES submission_groups(submission_group_id),
    ims_status TEXT CHECK (ims_status IN (
        'submitted',
        'declined',
        'in rating', 
        'lost',
        'not taken up',
        'cancelled',
        'bound-issued',
        'underwriting review',
        'referred to carrier',
        'bound',
        'expired',
        'not quoted',
        'pending cancellation'
        )),
    division TEXT CHECK (division IN (
        'Wholesale',
        'Habitational',
        'Non-Profit Package',
        'Religious',
        'Workers Compensation',
        'Other'
         ))
);

CREATE TABLE IF NOT EXISTS quotes (
    quote_id TEXT PRIMARY KEY,
    submission_control_number TEXT REFERENCES submissions(control_number),
    carrier_id TEXT REFERENCES carriers(carrier_id),
    quote_premium REAL,
    quote_status TEXT CHECK (quote_status IN (
        'quoted',
        'not quoted',
        'bound',
        'declined',
        'not taken up',
        'lost'
    ))
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    control_number TEXT REFERENCES submissions(control_number),
    carrier_id TEXT REFERENCES carriers(carrier_id),
    bound_premium REAL,
    policy_status TEXT CHECK (policy_status IN (
        'bound',
        'bound-issued',
        'expired',
        'cancelled',
        'pending cancellation'
    )) 
);       

CREATE TABLE IF NOT EXISTS losses (
    loss_id TEXT PRIMARY KEY,
    policy_id TEXT REFERENCES policies(policy_id),
    loss_date TEXT NOT NULL, /*DATE*/
    report_date TEXT NOT NULL, /*DATE*/
    paid_amount REAL, 
    reserved_amount REAL,
    incurred_amount REAL,
    loss_status TEXT CHECK (loss_status IN (
        'lost',
        'not taken up',
        'declined',
        'pending cancellation',
        'expired',
        'cancelled'
    ))
);


