from db_connection import connect_to_db
from datetime import datetime


def load_previous_data():
    """Fetch previous event data from the database."""
    connection = connect_to_db()
    if not connection:
        print("Error: Unable to connect to the database.")
        return {}

    cursor = connection.cursor()
    cursor.execute("SELECT id, event_date, teams, status FROM rcb_events")
    rows = cursor.fetchall()

    previous_data = {}
    for row in rows:
        event_id, event_date, teams, status = row
        date_str = event_date.strftime('%b %d, %Y %I:%M %p')
        previous_data[date_str] = {
            "id": event_id,
            "teams": teams,
            "status": status
        }

    cursor.close()
    connection.close()
    return previous_data


def parse_date(date_str):
    """Parse the date string, trying both formats."""
    for fmt in ["%a, %b %d, %Y %I:%M %p", "%b %d, %Y %I:%M %p"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    print(f"Error parsing date '{date_str}'.")
    return None


def save_current_data(new_data):
    """Insert or update the event data if it differs."""
    previous_data = load_previous_data()

    if not new_data:
        print("\n📁 No new data to save.")
        return

    try:
        connection = connect_to_db()
        if not connection:
            print("Error: Unable to connect to the database.")
            return

        cursor = connection.cursor()

        for event in new_data:
            date_str = event["date"]
            event_date = parse_date(date_str)
            if not event_date:
                continue

            teams = ", ".join(event["teams"])
            status = event["status"]
            formatted_date_str = event_date.strftime('%b %d, %Y %I:%M %p')

            if formatted_date_str in previous_data:
                existing_event = previous_data[formatted_date_str]
                if existing_event["status"] != status:
                    cursor.execute("""
                        UPDATE rcb_events
                        SET status = %s
                        WHERE id = %s
                    """, (status, existing_event["id"]))
                    print(f"\n📁 Event for {formatted_date_str} updated.")
            else:
                cursor.execute("""
                    INSERT INTO rcb_events (event_date, teams, status)
                    VALUES (%s, %s, %s)
                """, (event_date, event["teams"], status))
                print(f"\n📁 Event for {formatted_date_str} inserted.")

        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error saving the data to the database: {e}")


def load_held_data():
    """Fetch already held events from the database."""
    connection = connect_to_db()
    if not connection:
        print("Error: Unable to connect to the database.")
        return []

    cursor = connection.cursor()
    cursor.execute("SELECT event_date, teams, status FROM events_held")
    rows = cursor.fetchall()

    held_events = [{
        "date": row[0].strftime('%b %d, %Y %I:%M %p'),
        "teams": row[1],
        "status": row[2]
    } for row in rows]

    cursor.close()
    connection.close()
    return held_events


def get_emails():
    connection = connect_to_db()
    if not connection:
        print("Error: Unable to connect to the database.")
        return []

    cursor = connection.cursor()
    cursor.execute("SELECT email FROM email")  # Select only the 'email' column
    rows = cursor.fetchall()

    # Extract emails from the tuples
    emails = [row[0] for row in rows]

    cursor.close()
    connection.close()
    return emails


def find_new_status_events(events):
    """Find and insert new events whose status is not 'COMING SOON' or 'SOLD OUT'."""
    already_held = load_held_data()
    held_event_signatures = {
        (e['date'], tuple(e['teams']), e['status']) for e in already_held
    }

    new_events = [
        e for e in events if e['status'] not in ["COMING SOON", "SOLD OUT"] and
        (e['date'], tuple(e['teams']), e['status']) not in held_event_signatures
    ]

    if new_events:
        try:
            connection = connect_to_db()
            if not connection:
                print("Error: Unable to connect to the database.")
                return

            cursor = connection.cursor()
            for event in new_events:
                event_date = parse_date(event["date"])
                if event_date:
                    teams = ", ".join(event["teams"])
                    status = event["status"]

                    cursor.execute("""
                        INSERT INTO events_held (event_date, teams, status)
                        VALUES (%s, %s, %s)
                    """, (event_date, event["teams"], status))
                    print(
                        f"\n📁 Event for {event['date']} inserted into events_held.")

            connection.commit()
            cursor.close()
            connection.close()
            return new_events

        except Exception as e:
            print(f"Error saving the data to the database: {e}")
    else:
        print("\nNo new events to add.")
