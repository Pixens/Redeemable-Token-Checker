import datetime
import itertools
import random
import requests
import threading
import time
import os
import yaml


__config__ = yaml.safe_load(open('./config.yml', 'r'))
__proxies__ = open('./proxies.txt', 'r').read().splitlines()
__tokens__ = itertools.cycle(open('./tokens.txt', 'r').read().splitlines())

now = datetime.datetime.now()
folder = f'output/{now.strftime("%d-%m-%Y %H;%M")}'
os.makedirs(f'{folder}', exist_ok=True)


class Check:

    def __init__(self):

        self.headers = {
            "Accept": "*/*",
            "Accept-language": f"en-GB,en;q=0.9",
            "Authorization": "",
            "Content-type": "application/json",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": '"Not.A/Brand";v="24", "Chromium";v="119", "Google Chrome";v="119"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-GB",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLUdCIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzExOS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTE5LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiJodHRwczovL2Rpc2NvcmQuY29tIiwicmVmZXJyaW5nX2RvbWFpbiI6ImRpc2NvcmQuY29tIiwicmVmZXJyZXJfY3VycmVudCI6Imh0dHBzOi8vZGlzY29yZC5jb20iLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiJkaXNjb3JkLmNvbSIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjI0NzkyOSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbH0="
        }

    def check_token(self, tries=0):
        if tries > __config__["retries"]:
            raise Exception("Failed to check token for subscription.")

        token = next(__tokens__)
        self.headers.update({"Authorization": token.split(':')[-1]})
        proxies = None

        if __config__["proxies"]:
            proxies = {
                "http": f"http://{random.choice(__proxies__)}",
                "https": f"http://{random.choice(__proxies__)}"
            }

        try:
            response = requests.get("https://discord.com/api/v9/users/@me/billing/subscriptions?include_inactive=true", headers=self.headers, proxies=proxies)
        except requests.exceptions.RequestException:
            return self.check_token(tries+1)

        if response.status_code == 200 and '[]' in response.text:
            open(f"{folder}/valid-redeemable.txt", "a").write(f"{token}\n")
        elif response.status_code == 401:
            open(f"{folder}/invalid.txt", "a").write(f"{token}\n")
        elif "verify" in response.text:
            open(f"{folder}/locked.txt", "a").write(f"{token}\n")
        elif response.status_code == 200 and '[]' not in response.text:
            open(f"{folder}/valid-not-redeemable.txt", "a").write(f"{token}\n")
        elif response.status_code == 429:
            time.sleep(response.json()['retry_after'] if 'retry_after' in response.text else 5)
            return self.check_token(tries+1)
        else:
            return self.check_token(tries+1)

    def start(self):
        tokens = open('./tokens.txt', 'r').read().splitlines()
        for _ in tokens:
            while threading.active_count() > __config__["threads"]:
                time.sleep(0.01)
            threading.Thread(target=self.check_token).start()
            while threading.active_count() > 1:
                time.sleep(0.01)


if __name__ == "__main__":
    print('Running...')
    Check().start()
    print('Finished.')
