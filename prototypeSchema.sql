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
    sub_status TEXT CHECK (sub_status IN (
        'Additional Information Received',
        'Additional Information Request',
        'Bound',
        'Bound - Issued'
        'Cancelled',
        'Cancelled by Correction',
        'Declined',
        'Expired',
        'In Rating',
        'Indicated',
        'Lost',
        'Lost on BOR',
        'Non-Renewed',
        'Not Quoted',
        'Not Taken Up',
        'Pending Cancellation',
        'Pending Reinstatement',
        'Quoted',
        'Quoted not Bound',
        'Referred to Carrier',
        'Submitted',
        'Unbound Correction',
        'Unbound Endorsement',
        'Unbound Internal Correction',
        "Underwriting Review",
        "Unknown Status"
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
    control_number TEXT REFERENCES submissions(control_number),
    carrier_id TEXT REFERENCES carriers(carrier_id),
    quote_premium REAL,
    quote_status TEXT CHECK (quote_status IN (
        'Quoted',
        'Quoted not Bound',
        'Bound-Issued',
        'Bound',
        'Declined',
        'Not Taken Up',
        'Lost'
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
    loss_status TEXT CHECK (policy_status IN (
        'lost',
    ))
);


