import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from demo import save_current_data, find_new_status_events, get_emails

# Load environment variables from the .env file
load_dotenv()

smtp_host = os.getenv('EMAIL_HOST')
smtp_port = int(os.getenv('EMAIL_PORT'))
username = os.getenv('EMAIL_USER')
password = os.getenv('EMAIL_PASS')


options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)


def mail_alert():

    try:
        url = 'https://shop.royalchallengers.com/ticket'
        driver.get(url)

        # Wait for the page to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, 'rcb-shop')))

        # Parse the loaded page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        new_events = []

        # Find all event blocks dynamically
        event_blocks = soup.find_all('div', class_='css-q38j1a')

        for block in event_blocks:
            # Extract Date
            date_div = block.find('div', class_='css-b2t39r')
            date = date_div.find('p').get_text(
                strip=True) if date_div and date_div.find('p') else 'N/A'

            # Extract Teams
            teams = []
            team_divs = block.find_all('p', class_='chakra-text css-10rvbm3')
            for team_div in team_divs:
                teams.append(team_div.get_text(strip=True))

            # Handle special single-team events (like RCB UNBOX)
            if not teams:
                special_event = block.find(
                    'p', class_='chakra-text css-vahgqk')
                if special_event:
                    teams.append(special_event.get_text(strip=True))

            # Extract Status
            status_button = block.find('button')
            status = status_button.get_text(
                strip=True) if status_button else 'N/A'

            # Compile event info
            event_info = {
                "date": date,
                "teams": teams if teams else ["N/A"],
                "status": status
            }
            new_events.append(event_info)

        new_status_events = find_new_status_events(new_events)

        if new_status_events:
            print("\n🚨 ALERT! New events with active tickets detected:\n")

            # Prepare the responsive HTML email body
            email_body = """
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    @media only screen and (max-width: 600px) {
                        .container {
                            padding: 20px !important;
                        }
                        .table-header, .table-cell {
                            display: block;
                            width: 100% !important;
                            text-align: left !important;
                        }
                        .cta-button {
                            padding: 12px 20px !important;
                            font-size: 16px !important;
                        }
                        .header-text {
                            font-size: 24px !important;
                        }
                        .sub-text {
                            font-size: 16px !important;
                        }
                    }
                </style>
            </head>
            <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f7f9fc; padding: 50px;">
                <div class="container" style="background-color: #ffffff; padding: 40px; border-radius: 12px; border: 1px solid #e5e5e5; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05); max-width: 650px; margin: auto;">
                    
                    <!-- Header -->
                    <div style="text-align: center; margin-bottom: 30px;">
                        <img src="https://shop.royalchallengers.com/imgs/rcb-logo-new.png" alt="RCB Logo" style="max-width: 150px; height: auto;">
                        <h2 class="header-text" style="color: #d6336c; font-size: 32px; margin-top: 20px; font-weight: 600;">🚨 New Ticket Alert! 🚨</h2>
                        <p class="sub-text" style="font-size: 18px; color: #555555; line-height: 1.6; max-width: 500px; margin: auto;">Get ready for the next RCB match! Below are the latest updates on ticket availability for upcoming events.</p>
                    </div>
                <div style="text-align: center; margin-top: 30px;">
                        <a href="https://shop.royalchallengers.com/ticket" 
                        class="cta-button" 
                        style="background-color: #d6336c; color: white; padding: 15px 30px; font-size: 18px; font-weight: 600; border-radius: 8px; text-decoration: none; display: inline-block;">
                            Grab Your Tickets Now! 🎟️
                        </a>
                    </div>
                    <!-- Table -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; margin-top: 30px;">
                        <thead>
                            <tr>
                                <th class="table-header" style="background-color: #d6336c; color: #ffffff; padding: 12px 18px; text-align: left; font-weight: 600; font-size: 16px;">Date</th>
                                <th class="table-header" style="background-color: #d6336c; color: #ffffff; padding: 12px 18px; text-align: left; font-weight: 600; font-size: 16px;">Teams</th>
                                <th class="table-header" style="background-color: #d6336c; color: #ffffff; padding: 12px 18px; text-align: left; font-weight: 600; font-size: 16px;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
            """

            for event in new_status_events:
                email_body += f"""
                            <tr style="background-color: #f9f9f9; border-bottom: 1px solid #e5e5e5;">
                                <td class="table-cell" style="padding: 14px 20px; font-size: 16px; color: #333333;">{event['date']}</td>
                                <td class="table-cell" style="padding: 14px 20px; font-size: 16px; color: #333333;">{' vs '.join(event['teams'])}</td>
                                <td class="table-cell" style="padding: 14px 20px; font-size: 16px; color: #28a745; font-weight: bold;">{event['status']}</td>
                            </tr>
                """
                print(
                    f"🎟️ {event['date']} - {' vs '.join(event['teams'])} - Status: {event['status']}")

            email_body += """
                        </tbody>
                    </table>

                    <!-- Call to Action -->
                

                    <!-- Footer -->
                    <div style="margin-top: 40px; text-align: center; font-size: 14px; color: #888888;">
                        <p>This is an automated alert from <strong>RCB Tickets Alert</strong>.</p>
                        <p>&copy; 2025 Royal Challengers Bangalore | All Rights Reserved</p>
                    </div>

                </div>
            </body>
            </html>
            """

            # Prepare and send the email
            sender = username
            targets = get_emails()
            msg = MIMEText(email_body, 'html')
            msg['Subject'] = '🚨 TICKETS WAITING FOR YOU!'
            msg['From'] = "RCB Tickets Alert"
            msg['To'] = ', '.join(targets)

            try:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(username, password)
                    server.sendmail(sender, targets, msg.as_string())
                print("✅ Email sent successfully!")
            except Exception as email_error:
                print(f"❌ Failed to send email: {email_error}")

        else:
            print("✅ No new ticket sales detected.")

        # Save the updated data
        save_current_data(new_events)

    except Exception as e:
        print(f"❌ An error occurred: {e}")

    finally:
        driver.quit()
