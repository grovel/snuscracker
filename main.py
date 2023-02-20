import argparse
import json
import requests
from bs4 import BeautifulSoup

email_passes = {}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def crack_snusbase(term, values):
    response = requests.post('https://beta.snusbase.com', data={
        'term': values,
        'activation_code': 'sbYGVcYxGEuBQt2P51meLO9TpmvMhr',
        'type': term,
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table', class_='databaselist')

    print(bcolors.OKCYAN + "Cracking Passwords..." + bcolors.ENDC)

    for table in tables:
        rows = table.find_all('tr')
        email = None
        password = None

        for row in rows:
            columns = row.find_all('td')

            if len(columns) < 2:
                continue

            field = columns[0].text.strip().lower()
            value = columns[1].text.strip()

            if field == 'email':
                email = value
            elif field == 'password':
                password = value
            elif field == 'hash':
                hash_value = value
                hash_response = requests.get(
                    f'https://beta.snusbase.com/v1/hash/{hash_value}', headers={
                        "authorization": 'sbYGVcYxGEuBQt2P51meLO9TpmvMhr'
                    })

                try:
                    hash_json = hash_response.json()
                except json.JSONDecodeError:
                    continue

                if hash_json.get('found') == True:
                    print(bcolors.OKGREEN + f"Found Password: {hash_json.get('password')}" + bcolors.ENDC)
                    password = hash_json.get('password')

        if email and password:
            if email in email_passes:
                email_passes[email].append(password)
            else:
                email_passes[email] = [password]

    return email_passes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Search for leaked email passwords on Snusbase.')
    parser.add_argument('email', metavar='EMAIL', type=str,
                        help='the email to search for')
    args = parser.parse_args()

    email = args.email
    email_passes = crack_snusbase('email', [email])

    with open('email_passes.txt', 'w') as f:
        print(bcolors.OKCYAN + "Removing Dupes..." + bcolors.ENDC)
        for email, passwords in email_passes.items():
            passwords = list(set(passwords))

            for password in passwords:
                f.write(f"{email}:{password}\n")

        print(bcolors.OKGREEN + "Done, wrote to email_passes.txt" + bcolors.ENDC)
