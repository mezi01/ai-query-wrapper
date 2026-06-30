"""
-generate fake insurance data for testing
-includes intentional dirty data to practice cleaning

"""

import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)
DB_PATH = "prototype.db"

def make_dirty(value):
    choice = random.random()
    if choice < 0.15:
        return None
    elif choice < 0.30:
        return value.upper()
    elif choice < 0.45:
        return value.lower()
    elif choice < 0.55:
        return value + " "
    elif choice < 0.65:
        return value.replace("'", "")
    elif choice < 0.75:
        return value.replace(" ", "  ")
    else:
        return value
    
LOBS = [
    ("Auto-Commercial",),
    ("BOP",),
    ("Builders Risk",),
    ("Comprehensive Personal Liability",),
    ("Cyber",),
    ("Directors and Officers",),
    ("Dwelling Fire",),
     ("Employment Practices Liability",),
    ("Excess Casualty",),
    ("Excess Flood",),
    ("Excess Liability",),
    ("FNP Auto",),
    ("FNP E&S Excess",),
    ("FNP E&S Package",),
    ("General Liability",),
    ("General Liability - Discontinued Operations",),
    ("Habitational GL",),
    ("Mobile Home",),
    ("Occupational Accident",),
    ("Package",),
    ("Package Policy",),
    ("Primary Flood - Residential",),
    ("Professional Liability",),
    ("Property",),
    ("Religious Institutions Auto",),
    ("Religious Institutions E&S GL",),
    ("Religious Institutions E&S Package",),
    ("Religious Institutions E&S PROP",),
    ("Religious Institutions Package",),
    ("Renters",),
    ("Sexual Molestation Liability",),
    ("TRIA",),
    ("Umbrella",),
    ("Wind/Hail Deductible Buy Back",),
    ("Worker's Compensation",)
]

LOB_DIVISION_MAP = {
    "Auto-Commercial": ["Religious", "Non-Profit Package" , "Wholesale", "Other"],
    "BOP": ["Religious", "Wholesale", "Other"],
    "Builders Risk": ["Wholesale"],
    "Comprehensive Personal Liability": ["Other"],
    "Cyber": ["Non-Profit Package", "Wholesale", "Other"],
    "Directors and Officers": ["Religious", "Non-Profit Package", "Wholesale", "Other"],
    "Dwelling Fire": ["Other"],
    "Employment Practices Liability": ["Wholesale", "Other"],
    "Excess Casualty": ["Wholesale", "Other"],
    "Excess Flood": ["Non-Profit Package"],
    "Excess Liability": ["Other"],
    "FNP Auto": ["Non-Profit Package"],
    "FNP E&S Excess": ["Non-Profit Package"],
    "FNP E&S Package": ["Non-Profit Package"],
    "General Liability": ["Religious", "Non-Profit Package", "Wholesale", "Other"],
    "General Liability - Discontinued Operations": ["Wholesale"],
    "Habitational GL": ["Habitational", "Wholesale", "Other"],
    "Mobile Home": ["Other"],
    "Occupational Accident": ["Wholesale"],
    "Package": ["Religious", "Non-Profit Package", "Habitational", "Wholesale", "Other"],
    "Package Policy": ["Non-Profit Package", "Wholesale", "Other"],
    "Primary Flood - Residential": ["Non-Profit Package"],
    "Professional Liability": ["Wholesale", "Other"],
    "Property": ["Religious", "Non-Profit Package", "Wholesale", "Other"],
    "Religious Institutions Auto": ["Religious", "Non-Profit Package", "Other"],
    "Religious Institutions E&S GL": ["Religious"],
    "Religious Institutions E&S Package": ["Religious"],
    "Religious Institutions E&S PROP": ["Religious"],
    "Religious Institutions Package": ["Religious", "Other"],
    "Renters": ["Other"],
    "Sexual Molestation Liability": ["Wholesale", "Other"],
    "TRIA": ["Wholesale"],
    "Umbrella": ["Religious", "Non-Profit Package", "Habitational", "Wholesale", "Other"],
    "Wind/Hail Deductible Buy Back": ["Wholesale", "Other"],
    "Worker's Compensation": ["Religious", "Non-Profit Package", "Wholesale", "Other", "Workers Compensation"],
}

"""
LOBS = [
    ("Auto-Commercial",),
    ("BOP",),
    ("Builders Risk",),
    ("Comprehensive Personal Liability",),
    ("Cyber",),
    ("Deductible Buy back",),
    ("Directors and Officers",),
    ("Dwelling Fire",),
    ("Earthquake",),
    ("Employment Practices Liability",),
    ("Excess Casualty",),
    ("Excess Comprehensive Personal Liability",),
    ("Excess Flood",),
    ("Excess Liability",),
    ("FL Homeowners with Wind",),
    ("FNP Auto",),
    ("FNP E&S Excess",),
    ("FNP E&S Package",),
    ("General Liability - Discontinued Operations",),
    ("General Liability",),
    ("Habitational GL",),
    ("Homeowners",),
    ("Inland Marine",),
    ("Mobile Home",),
    ("Motor Home",),
    ("Motorcycle",),
    ("Package",),
    ("Package Policy",),
    ("Personal Articles Floater",),
    ("Personal Auto",),
    ("Personal Excess Umbrella",),
    ("Personal Umbrella",),
    ("Pollution Liability",),
    ("Premier Home",),
    ("Primary Flood - Commercial",),
    ("Primary Flood - Residential",),
    ("Professional Liability",),
    ("Property",),
    ("Religious Institutions Auto",),
    ("Religious Institutions E&S GL",),
    ("Religious Institutions E&S Package",),
    ("Religious Institutions E&S PROP",),
    ("Religious Institutions Package",),
    ("Renters",),
    ("Sexual Molestation Liability",),
    ("TRIA",),
    ("Umbrella",),
    ("Wind Only",),
    ("Wind/Hail Deductible Buy Back",),
    ("Worker's Compensation",),
]
"""
CARRIERS = [
    ("CAR001", "A.I.M. Mutual Insurance Co.", fake.name()),
    ("CAR002", "Admiral Insurance Company", fake.name()),
    ("CAR003", "AIG Property Casualty Company", fake.name()),
    ("CAR004", "Alpha Property & Casualty Insurance Co", fake.name()),
    ("CAR005", "American Bankers Insurance Company of FL", fake.name()),
    ("CAR006", "AmGUARD Insurance Company", fake.name()),
    ("CAR007", "AmTrust Insurance Co of Kansas", fake.name()),
    ("CAR008", "AmTrust North America Inc.", fake.name()),
    ("CAR009", "Arch Insurance Company", fake.name()),
    ("CAR010", "ARI Insurance Company", fake.name()),
    ("CAR011", "Aspen American Insurance Company", fake.name()),
    ("CAR012", "Aspen Specialty Insurance Company", fake.name()),
    ("CAR013", "Associated Industries Insurance Company", fake.name()),
    ("CAR014", "Axis Insurance Company", fake.name()),
    ("CAR015", "AXIS Surplus Insurance Company", fake.name()),
    ("CAR016", "Benchmark Insurance Company", fake.name()),
    ("CAR017", "Berkley National Insurance Company", fake.name()),
    ("CAR018", "Berkley National Insurance Company - Senior Living Admitted", fake.name()),
    ("CAR019", "Berkley Specialty Insurance Company - Senior Living E & S", fake.name()),
    ("CAR020", "Berkley Specialty Insurance Company -- E & S Non-Profit", fake.name()),
    ("CAR021", "Blue Ridge Indemnity Insurance", fake.name()),
    ("CAR022", "BMS Group", fake.name()),
    ("CAR023", "Boost.io", fake.name()),
    ("CAR024", "Bristol West Insurance Company", fake.name()),
    ("CAR025", "Business Risk Partners", fake.name()),
    ("CAR026", "Capitol Specialty Insurance Corporation", fake.name()),
    ("CAR027", "Carolina Casualty Insurance Company", fake.name()),
    ("CAR028", "Century Surety Co", fake.name()),
    ("CAR029", "Certain Underwriters at Lloyd's -Coalition", fake.name()),
    ("CAR030", "Certain Underwriters at Lloyds", fake.name()),
    ("CAR031", "Charter Indemnity Co", fake.name()),
    ("CAR032", "Chubb Indemnity Insurance Company", fake.name()),
    ("CAR033", "Chubb Insurance Company of New Jersey", fake.name()),
    ("CAR034", "Church Mutual Insurance Company - Non-Profit Program", fake.name()),
    ("CAR035", "Church Mutual Insurance Company - Religious COE", fake.name()),
    ("CAR036", "Clearance Carrier", fake.name()),
    ("CAR037", "CM Regent Insurance Company",fake.name()),
    ("CAR038", "CM Vantage Specialty Insurance Company", fake.name()),
    ("CAR039", "CNA", fake.name()),
    ("CAR040", "CO/ACTION Specialty Insurance Group",fake.name()),
    ("CAR041", "Coast National Insurance Company", fake.name()),
    ("CAR042", "Convex Insurance UK Limited", fake.name()),
    ("CAR043", "Dairyland County Mutual Insurance Company of Texas", fake.name()),
    ("CAR044", "Dairyland Insurance Company", fake.name()),
    ("CAR045", "Drive New Jersey Insurance Company", fake.name()),
    ("CAR046", "Employers Assurance Co - Healthcare", fake.name()),
    ("CAR047", "Employers Assurance Co - Non-Profit", fake.name()),
    ("CAR048", "Employers Assurance Company", fake.name()),
    ("CAR049", "Employers Compensation Ins Co - Healthcare", fake.name()),
    ("CAR050", "Employers Compensation Ins Co - Non-Profit", fake.name()),
    ("CAR051", "Employers Preferred Insurance Company", fake.name()),
    ("CAR052", "Endurance American Specialty Insurance Company", fake.name()),
    ("CAR053", "Evanston Insurance Company", fake.name()),
    ("CAR054", "Federal Insurance Company", fake.name()),
    ("CAR055", "Financial Indemnity Company", fake.name()),
    ("CAR056", "Foremost County Mutual Insurance Company", fake.name()),
    ("CAR057", "Foremost Insurance Company", fake.name()),
    ("CAR058", "Foremost Lloyds of TX", fake.name()),
    ("CAR059", "Fortegra Specialty Insurance Company", fake.name()),
    ("CAR060", "General Star Indemnity Company", fake.name()),
    ("CAR061", "Great American Insurance Company", fake.name()),
    ("CAR062", "Guard", fake.name()),
    ("CAR063", "Guard Insurance Company", fake.name()),
    ("CAR064", "GuideOne Elite Insurance Company", fake.name()),
    ("CAR065", "GuideOne Mutual Insurance Company", fake.name()),
    ("CAR066", "GuideOne National Insurance Company", fake.name()),
    ("CAR067", "GuideOne Specialty Insurance Company", fake.name()),
    ("CAR068", "Hadron Specialty Insurance Company", fake.name()),
    ("CAR069", "Harleysville Insurance Company", fake.name()),
    ("CAR070", "Harleysville Worcester Ins Co", fake.name()),
    ("CAR071", "Hartford Casualty Ins Co", fake.name()),
    ("CAR072", "Highview National Insurance Company", fake.name()),
    ("CAR073", "Houston Casualty Company", fake.name()),
    ("CAR074", "Hudson Excess Ins Co - Corvus", fake.name()),
    ("CAR075", "Hudson Excess Insurance Company", fake.name()),
    ("CAR076", "Hudson Insurance Company", fake.name()),
    ("CAR077", "Hudson Specialty Insurance Company", fake.name()),
    ("CAR078", "Insurance Company of the South", fake.name()),
    ("CAR079", "Insurmark/Floodwatch", fake.name()),
    ("CAR080", "Ironshore Europe Limited/Certain Underwriters at Lloyds", fake.name()),
    ("CAR081", "Ironshore Specialty Insurance Company", fake.name()),
    ("CAR082", "Kinsale Insurance Company", fake.name()),
    ("CAR083", "Lexington Insurance Co", fake.name()),
    ("CAR084", "Lexington Insurance Company", fake.name()),
    ("CAR085", "LIO Insurance Group", fake.name()),
    ("CAR086", "Lloyd's of London - Beazley Syndicate #2323/0623", fake.name()),
    ("CAR087", "Lloyds of London", fake.name()),
    ("CAR088", "Lyndon Southern Insurance Company", fake.name()),
    ("CAR089", "Markel Ins Company", fake.name()),
    ("CAR090", "Markel Insurance Company", fake.name()),
    ("CAR091", "Middlesex Insurance Company", fake.name()),
    ("CAR092", "Motor Transport Mutual RRG", fake.name()),
    ("CAR093", "Moxie Series (Admitted)", fake.name()),
    ("CAR094", "National Continental Insurance Company", fake.name()),
    ("CAR095", "National General Insurance Company", fake.name()),
    ("CAR096", "North American Capacity Ins Co", fake.name()),
    ("CAR097", "North American Specialty Insurance Corporation", fake.name()),
    ("CAR098", "Pacific Indemnity Company", fake.name()),
    ("CAR099", "Palms Insurance Company, Ltd", fake.name()),
    ("CAR100", "Peak Property and Casualty Insurance Corporation", fake.name()),
    ("CAR101", "Pennsylvania Manufacturers Assoc. Insurance Co", fake.name()), 
    ("CAR102", "Privilege Underwriters Reciprocal Exchange", fake.name()),
    ("CAR103", "Progressive Casualty Insurance Company", fake.name()),
    ("CAR104", "Progressive County Mutual Insurance Co", fake.name()),
    ("CAR105", "PURE Programs, LLC", fake.name()), 
    ("CAR106", "Quantum Series", fake.name()), 
    ("CAR107", "Reliable Lloyds Insurance Company", fake.name()),
    ("CAR108", "Republic-Vanguard Insurance Company", fake.name()),
    ("CAR109", "Risk Smith", fake.name()), 
    ("CAR110", "Rochdale Ins Co Of NY", fake.name()),
    ("CAR111", "Security National Insurance Co", fake.name()), 
    ("CAR112", "Sentry Insurance a Mutual Company", fake.name()), 
    ("CAR113", "Sequoia Ins Co", fake.name()),
    ("CAR114", "Sompo", fake.name()),
    ("CAR115", "StarStone National Insurance Company", fake.name()),
    ("CAR116", "Surya Ins Company - NEMT", fake.name()),
    ("CAR117", "Technology Ins Co Inc", fake.name()),
    ("CAR118", "Templar Series", fake.name()),
    ("CAR119", "The Hartford", fake.name()),
    ("CAR120", "The Hartford - VCAP", fake.name()),
    ("CAR121", "Travelers Excess and Surplus LInes Company", fake.name()),
    ("CAR122", "Unitrin County Mutual Insurance Co", fake.name()),
    ("CAR123", "Vigilant Insurance Company", fake.name()),
    ("CAR124", "Viking Insurance Company of Wisconsin", fake.name()),
    ("CAR125", "Wesco Ins Co", fake.name()),
    ("CAR126", "Westchester, A Chubb Company", fake.name()),
    ("CAR127", "Wyvern Series (Admitted)", fake.name()),
    ("CAR128", "Wyvern Series (Non-Admitted)", fake.name())

]
"""
(broker_id, producer_name, producer_state, relationship_owner)
found 907 distinct producers so I'm generating 200 fake ones 
"""
BROKERS = [
    (f"BRK{str(i).zfill(3)}", fake.name(), make_dirty(fake.state_abbr()), make_dirty(fake.name()))
    for i in range(1, 201)
]


# found over 5000 distinct account names so generating fake ones 



TYPES = [
    "New",
    "Broker on Record (BOR)",
    "Courtesy Filing",
    "Purchased Book of Business",
    "Renewal",
    "Rewrite",
    "Roll-Over"
]

PRIORITIES = [
    "Null",
    "0 - No opportunity, log in only ?Does not fit appetite",
    "1 - Received application and some loss data, account not qualified",
    "2 - Received application, account qualified ? Additional info requested to complete file",
    "3 - Fully qualified submission with all required information obtained from the broker-No commitment from Broker",
    "4 - Fully complete submission with broker requirements to bind and will be recommended -Broker New opportunity",
    "5 - Fully complete submission with broker requirements to bind and will be recommended ? Broker Controls"
]

IMS_STATUSES = [
    "submitted",
    "declined",
    "in rating",
    "lost",
    "not taken up",
    "cancelled",
    "bound-issued",
    "underwriting review",
    "referred to carrier",
    "bound",
    "expired",
    "not quoted",
    "pending cancellation"
]

QUOTE_STATUSES = [
    "quoted",
    "not quoted",
    "bound",
    "declined",
    "not taken up",
    "lost"
]

POLICY_STATUSES = [
    "bound",
    "bound-issued",
    "expired",
    "cancelled",
    "pending cancellation"
]

LOSS_STATUSES = [
    "open",
    "closed",
    "closed without payment",
    "reopened",
    "litigation"
]

DIVISIONS = [
    "Wholesale",
    "Habitational",
    "Non-Profit Package",
    "Religious",
    "Workers Compensation",
    "Other"
]

def build_accounts(n=500):
    rows = []
    for i in range(1, n+1):
        premium = round(random.uniform(0, 1000000), 2)
        if premium < 10000:
            tier = "Small"
        elif premium < 250000:
            tier = "Medium"
        else:
            tier = "Large"
        account_name = fake.company()
        rows.append((f"ACC{str(i).zfill(3)}",
            make_dirty(account_name),  #dirty
            account_name,              #clean
            tier,
        ))
    return rows

def build_submission_groups(accounts):
    rows = []
    for account in accounts:
        
       # 1. randomly picks how many submission groups this account will have -> 1, 2, 3
       # 2. loops based on # of sub_groups
       # 3. generate group submision number 
       # 4. generates a random decimal number 0-20,000,000 for target_premium
        
        # how many groups per account
        n_groups = random.randint(1,3)
        for i in range(n_groups):
            rows.append((
               (f"GRP{str(len(rows)+1).zfill(4)}"),
               round(random.uniform(0, 20000000), 2),
               account[0],
               random.choice(BROKERS)[0]
            ))

    return rows
    
def build_submissions(submission_groups): 
    rows = []
    today = datetime.today()
    start = today.replace(month=1, day=1)
    end = today.replace(month=12, day=31)
    for i,  group in enumerate(submission_groups):
            # how many submissions per group; same pattern as n_groups just one level deeper 
        n_submissions = random.randint(1,5) 
        for j in range(n_submissions):
            eff = fake.date_between(start_date=start, end_date=end)
            exp = eff + timedelta(days=365)
            lob_name = random.choice(LOBS)[0]
            rows.append((
                (f"CON{str(i).zfill(3)}{str(j).zfill(2)}"), 
                group[2],
                random.choice(BROKERS)[0],
                lob_name,
                eff.strftime("%Y-%m-%d"),
                exp.strftime("%Y-%m-%d"),
                round(random.uniform(0, 20000000), 2),
                random.choice(PRIORITIES),
                random.choice(TYPES),
                group[0],
                random.choices(IMS_STATUSES, weights=[30, 25, 5, 5, 5, 5, 5, 3, 3, 3, 3, 3, 2], k=1)[0],
                random.choice(LOB_DIVISION_MAP.get(lob_name, DIVISIONS))
                ))
            
    return rows
        
def build_quotes(submissions):
        rows = []
        for i, submission in enumerate(submissions):
            n_quotes = random.randint(1,3)
            for j in range(n_quotes):
                rows.append((
                    (f"QUO{str(i).zfill(3)}{str(j).zfill(2)}"),
                    submission[0],
                    random.choice(CARRIERS)[0],
                    round(random.uniform(0, 20000000), 2),
                    random.choices(QUOTE_STATUSES, weights=[12, 53, 25, 5, 7, 3], k=1)[0]
                ))    
        return rows 
            
def build_policies(quotes):
        rows = []
        for i, quote in enumerate(quotes):
            if quote[4] in ("bound", "bound-issued"):
                rows.append((
                    (f"POL{str(i).zfill(3)}"),
                    quote[1],
                    quote[2],
                    round(random.uniform(5000, 500000), 2),
                    random.choices(POLICY_STATUSES, weights = [25, 28, 20, 15, 12], k=1)[0]
                ))
        return rows        
    
def build_losses(policies):
        rows = []
        for i, policy in enumerate(policies):
            if random.random() < 0.25: 
               loss_date = fake.date_between(
                   start_date = datetime(2024, 1, 1),
                   end_date = datetime.today())
               report_date = fake.date_between(
                   start_date = loss_date,
                   end_date = datetime.today())
               paid_amount = round(random.uniform(0, 500000), 2)
               reserved_amount = round(random.uniform(0, 500000), 2)
               incurred_amount = round(paid_amount + reserved_amount, 2)
               rows.append((
                    (f"LOS{str(i).zfill(3)}"),
                    policy[0],
                    loss_date.strftime("%Y-%m-%d"),
                    report_date.strftime("%Y-%m-%d"),
                    paid_amount,
                    reserved_amount,
                    incurred_amount,
                    random.choices(LOSS_STATUSES, weights = [40, 35, 15, 5, 5], k=1)[0]
                ))
        return rows
    
def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open("prototypeSchema.sql") as f:
        conn.executescript(f.read())

    cur.executemany("INSERT OR REPLACE INTO lines_of_business VALUES (?)", LOBS)
    cur.executemany("INSERT OR REPLACE INTO brokers VALUES (?,?,?,?)", BROKERS)
    cur.executemany("INSERT OR REPLACE INTO carriers VALUES (?,?,?)",CARRIERS)


    accounts = build_accounts(500)
    cur.executemany("INSERT OR REPLACE INTO accounts VALUES (?,?,?,?)", accounts)

        # transactional data in dependency order 
        # each build_ fct receives its parent as a parameter
        # ? must match the number of fields in data schema per table
    submission_groups = build_submission_groups(accounts)
    cur.executemany("INSERT OR REPLACE INTO submission_groups VALUES (?,?,?,?)", submission_groups)

    submissions = build_submissions(submission_groups)
    cur.executemany("INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", submissions)

    quotes = build_quotes(submissions)
    cur.executemany("INSERT OR REPLACE INTO quotes VALUES (?,?,?,?,?)", quotes)

    policies = build_policies(quotes)
    cur.executemany("INSERT OR REPLACE INTO policies VALUES (?,?,?,?,?)", policies)

    losses = build_losses(policies)
    cur.executemany("INSERT OR REPLACE INTO losses VALUES (?,?,?,?,?,?,?,?)", losses)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed()
