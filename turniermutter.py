import time
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
from datetime import datetime, timedelta

# --- CONFIGURATIONS ---
COOKIE_VALUE = os.environ.get("JUNIEN_INTRANET_LK_COOKIE_VALUE", "")
JUNIENTE = int(os.environ.get("JUNIEN_NUMMER", 28))
BASE_URL = "https://www.junien.net/"
TARGET_URL = f"https://www.junien.net/turnier/event/{JUNIENTE}/mytourneys/"
TELEGRAM_BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"
CHECK_INTERVAL_MINS = max(1, int(os.environ.get("STATUSCHECK_MINUTES", 5)))
CHECK_INTERVAL = CHECK_INTERVAL_MINS * 60
# ---------------------

def send_notification(message):
    try:
        payload = {
            'chat_id': TELEGRAM_CHAT,
            'text': message,
            'parse_mode': 'HTML'
        }
        print(f"INFO: Sending Telegram payload: {payload}")

        response = requests.post(TELEGRAM_API_URL, data=payload, timeout=10)

        print(f"INFO: Telegram API Response Status: {response.status_code}")
        #print(f"DEBUG: Telegram API Response Body: {response.text}")

        response.raise_for_status()
    except Exception as e:
        print(f"ERROR: Error sending to Telegram API: {e}")

def scrape():
    headers = {'Cookie': f"lk={COOKIE_VALUE}"}
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code} for {TARGET_URL}")
        response.raise_for_status()
    except Exception as e:
        print(f"Fetch error: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    found_nodes = {}

    # DEBUG: Print all div class='title' contents to logs
    all_titles = soup.find_all('div', class_='title')
    print(f"INFO: Found {len(all_titles)} elements with class='title'")
    for i, t in enumerate(all_titles):
        print(f"INFO: Title {i} content: '{t.get_text(strip=True)}'")

    # DEBUG: Print start of HTML to logs
    #print(f"DEBUG: Response start: {response.text[:10000].replace(chr(10), ' ')}")

    # Find the "Angemeldet" title div (use lambda for partial/whitespace match)
    title_div = soup.find('div', class_='title', string=lambda x: x and 'Angemeldet' in x)
    if not title_div:
        print("NOTICE: Keine 'Angemeldet' Tabellen im HTML DOM.")
        return {}

    # Iterate siblings (tables) after the title div
    current = title_div.next_sibling
    tables_found = 0
    while current:
        if current.name == 'table':
            tables_found += 1
            # We look for tables containing tournament info
            # The structure has <tr><td><table class="msg2">...
            # The target info is in msgrow2
            msgrow2 = current.find('td', class_='msgrow2')
            if msgrow2:
                # Extract Link: Find the <a> in msgrow1, which is the true tournament link
                link = None
                img_tag = current.find('td', class_='msgrow1').find('img') if current.find('td', class_='msgrow1') else None
                img_src = urllib.parse.urljoin(BASE_URL, img_tag['src']) if img_tag and img_tag.get('src') else None

                # The primary tournament link is actually in the msgrow1 cell's anchor
                primary_link_tag = current.find('td', class_='msgrow1').find('a', href=True)
                if primary_link_tag:
                    link = urllib.parse.urljoin(BASE_URL, primary_link_tag['href'])

                # Extract Image
                img_tag = current.find('td', class_='msgrow1').find('img') if current.find('td', class_='msgrow1') else None
                img_src = urllib.parse.urljoin(BASE_URL, img_tag['src']) if img_tag and img_tag.get('src') else None

                # Extract Title
                title_span = msgrow2.find('b')
                title = title_span.get_text(strip=True) if title_span else "Unbekannt"

                # Extract Status (e.g., "angemeldet: 15 / 16 -- Anmeldung gestartet")
                # Located in a nested table within msgrow2
                status_td = msgrow2.find('td', string=lambda x: x and 'angemeldet' in x.lower())
                if not status_td:
                    # Fallback: find the nested table and look for text
                    nested_table = msgrow2.find('table')
                    status_td = nested_table.find('td') if nested_table else None

                status = status_td.get_text(strip=True) if status_td else "Status unbekannt"

                # Extract Date/Time (Start: <b>24.10. 15:00</b>)
                current_year = datetime.now().year
                time_val = "Zeit unbekannt"
                raw_time = "Zeit unbekannt"
                # Search all <td> within the nested table of msgrow2
                all_tds = msgrow2.find_all('td')
                for td in all_tds:
                    if 'Start:' in td.get_text():
                        b_tag = td.find('b')
                        if b_tag:
                            raw_time = b_tag.get_text(strip=True)
                            display_val = raw_time
                            try:
                                # Split "24.10. 21:30" into "24.10." and "21:30"
                                date_part, time_part = raw_time.split(' ', 1)
                                clean_date = date_part.strip('.')

                                parsed_date = datetime.strptime(clean_date, "%d.%m").replace(year=current_year)
                                today = datetime.now().date()
                                target = parsed_date.date()

                                if target == today:
                                    display_val = "Heute"
                                elif target == today + timedelta(days=1):
                                    display_val = "Morgen"
                                else:
                                    display_val = raw_time

                                time_val = display_val # Use the processed display value
                            except (ValueError, IndexError):
                                time_val = raw_time
                            break # Exit loop once found

                # Use link as unique ID
                if link:
                    found_nodes[link] = {
                        'title': title,
                        'img': img_src,
                        'status': status,
                        'time': time_val,
                        'time_raw': raw_time
                    }

        current = current.next_sibling

    if tables_found == 0:
        print("No tournament tables found after 'Angemeldet' title.")
    else:
        print(f"Successfully parsed {tables_found} tournament tables.")

    return found_nodes

def main():
    print(f"Starting monitor for ['ju:nien] {JUNIENTE} Turniere...")
    previous_state = {}

    while True:
        current_state = scrape()

        # First run: Zusammenfassung aller Turniere
        if not previous_state:
            print(f"INFO: First fetch complete. Baseline established with {len(current_state)} tournaments.")
            if current_state:
                active_list = []
                finished_list = []
                for link, data in current_state.items():
                    if 'abgeschlossen' in data['status'].lower():
                        line = f"<a href='{link}'><b>{data['title']}</b></a>\n"
                        finished_list.append(line)
                    else:
                        line = f"<a href='{link}'><b>{data['title']}</b></a>\n@ <code>{data['time']}</code>\n{data['status']}\n"
                        active_list.append(line)

                summary_msg = "👀 ['ju:nien] Turnier Mutter\n\n"
                if active_list:
                    summary_msg += active_list
                if finished_list:
                    summary_msg += "\n\n<blockquote expandable>🏁 Abgeschlossen:\n" + "\n".join(finished_list) + "</blockquote>"

                send_notification(summary_msg)
        # Subsequent runs (nur Änderungen)
        else:
            print(f"INFO: Checking for updates. Found {len(current_state)} active tournaments.")
            # Check for changes
            for link, data in current_state.items():
                if link not in previous_state:
                    # New tournament found
                    msg = f"☑️ ['ju:nien] Neues Turnier:\n\n<b>{data['title']}</b>\n@ {data['time']}\n<a href='{link}'>{data['status']}</a>"
                    send_notification(msg)
                else:
                    # Check if status or time changed
                    old = previous_state[link]
                    status_changed = data['status'] != old['status']
                    time_changed = data['time_raw'] != old['time_raw']

                    if time_changed or status_changed:
                        time_info = ""
                        status_info = ""

                        if time_changed:
                            time_info = f"NEU @ <b>{data['time']}</b> <strike>{old['time']}</strike>"

                        if status_changed:
                            status_info = f"(NEU: {data['status']})"

                        if 'abgeschlossen' in data['status'].lower():
                            msg = f"🏁 ['ju:nien] Turnier fertig:\n\n<a href='{link}'><b>{data['title']}</b></a>\n{status_info}"
                            send_notification(msg)
                        else:
                            msg_parts = [f"🔔 ['ju:nien] Turnier Update:\n\n<a href='{link}'><b>{data['title']}</b></a>"]
                            if time_info: msg_parts.append(time_info)
                            if status_info: msg_parts.append(status_info)
                            send_notification("\n".join(msg_parts))

            # Check for removals (optional, but good for completeness)
            for link in previous_state:
                if link not in current_state:
                    send_notification(f"👋🏻 ['ju:nien] Turnier vorbei oder entfernt:\n<a href='{previous_state[link]}'><b>{previous_state[link]['title']}</b></a>\n({previous_state[link]['time']})")

        previous_state = current_state
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
