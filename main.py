import threading
from dotenv import load_dotenv
import os
import sys
from pandas import array
import requests
import json
import urllib3
import time
from colorama import Fore, Style
from pprint import pprint
from apscheduler.schedulers.blocking import BlockingScheduler
urllib3.disable_warnings()

class Session():
    def __init__(self, etherscan_api_key, address, proxy=None) -> None:
        self.etherscan_api_key = etherscan_api_key
        self.address = address
        self.Session = requests.Session()
        self.Session.verify = False
        if proxy != None: #if no proxy found, the program will use local IP
            a = proxy.split(':')
            proxy = '{}:{}@{}:{}'.format(a[2], a[3], a[0], a[1])
            self.Session.proxies = {
                "http": "http://" + proxy,
                "https": "http://" + proxy
            }
        self.endpoint = 'https://api.etherscan.io/api'
        self.getHash()

    def log(self, message, error=None):
        if (error):
            print(Fore.RED + f"{error}")
        print(f"{Fore.YELLOW}{message}", end=f'{Fore.MAGENTA}\n↳ ')
        sys.stdout.flush()

    def block(self):
        ts = time.time()
        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': str(ts).split('.', 1)[0],
            'closest': 'before',
            'apikey': self.etherscan_api_key
        }
        try:
            self.log('Getting Block Number')
            r = self.Session.get(self.endpoint, params=params)
            print(r.json()['result'])
            return r.json()['result']
        except Exception as e:
            self.log(e)

    def getHash(self):
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': self.address,
            'startblock': self.block(),
            'endblock': '50000000',
            'page': '1',
            'offset': '5',
            'sort': 'desc',
            'apikey': self.etherscan_api_key
        }
        self.log('Getting Hash')
        r = self.Session.get(self.endpoint, params=params)
        if r.json()['status'] == '0':
            print(Fore.RED + 'No Recent Tx Found')
        else:
            try:
                r = self.Session.get(self.endpoint, params=params)
                for a in (r.json()['result']): #loop through every tx from r
                    lastestTx = {
                        "Hash": [a][0]['hash'],
                        "From": [a][0]['from'],
                        "To": [a][0]['to'],
                        "Value": "{} ETH".format(round((10**-18) * int([a][0]['value']), 3)),
                        "Gas": "{} Gwei".format(round((10**-9) * int([a][0]['gasPrice']), 3)),
                        "isError": "Cancelled" if [a][0]['isError'] == '1' else "None"
                    }
                    #self.displayTx(lastestTx) #turn this on if you would like the program to write the output in terminal
                    self.webhook(lastestTx)
            except Exception as e:
                self.log('Failed', e)

    def displayTx(self, data: array):
        for element in data:
            cancel = True if data[element] == '1' else False
            self.log(element)
            print(data[element])

    def webhook(self, data):
        payload = {
            "embeds": [
                {
                    "title": "Tx Found",
                    "url": f"https://etherscan.io/tx/{data['Hash']}",
                    "color": '1169909',
                    "fields": [
                        {
                            "name": "From",
                            "value": data['From']
                        },
                        {
                            "name": "To",
                            "value": data['To']
                        },
                        {
                            "name": "Hash",
                            "value": data['Hash']
                        },
                        {
                            "name": "Amount",
                            "value": data['Value'],
                            "inline": 'true'
                        },
                        {
                            "name": "Gas",
                            "value": data['Gas'],
                            "inline": 'true'
                        }
                    ],
                    "footer": {
                        "text": "Powered by chili#9999"
                    }
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        #send a webhook to discord
        r = requests.post(
            discord_webhook, data=json.dumps(payload), headers=headers)

def run():
    with open('./appdata/ethAddress', 'r') as f:
        addresses = f.read().split('\n')
    threads = []
    for address in addresses: #Create a thread with every addess from "addresses"
        threads.append(threading.Thread(
            target=Session, args=[etherscan_api_key, address, proxy if proxy else None]))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    load_dotenv()
    print(Style.RESET_ALL)
    os.system('cls' if os.name == 'nt' else 'clear')
    etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
    discord_webhook = os.getenv('DISCORD_WEBHOOK')
    proxy = os.getenv('PROXY')
    while True: #Recall run() every 5 seconds.
        try:
            run()
            time.sleep(5)
        except KeyboardInterrupt:
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
