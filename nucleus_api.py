import base64
import pandas as pd
import requests

requests.packages.urllib3.disable_warnings()

#
# **** Define Class ****
#

# New Nucleus Class
class Nucleus_API:

    # Constructor
    def __init__(self, project_id, debug=False):
        self.findings_df = pd.DataFrame()
        self.scans_df = pd.DataFrame()

        self.project_id = str(project_id)

        with open('nucleus_api_key.txt', 'r') as f:
            base64_string = f.readline().strip()

        self.api_key = base64.b64decode(base64_string).decode('utf-8')

        self.api_url = "https://nucleus-uk1.nucleussec.com/nucleus/api"
        self.headers = {
            "x-apikey": self.api_key, 
            "accept": "application/json", 
            "cache-control": "no-cache"
            }
        
        self.debug = debug


    # API Functions
    # *** Should wrap in try...!

    def fetch_api_get (self, url):

        if self.debug:
            print (f"Fetching GET {url}")

        result = requests.get (url=url, headers=self.headers, verify=False)
        
        if self.debug:
            print (f"Status Code: {result.status_code}")
        
        return result
    

    def fetch_api_post (self, url, body):
        
        if self.debug:
            print (f"Fetching POST {url}")
        
        result = requests.post (url=url, headers=self.headers, verify=False, json=body)
        
        if self.debug:
            print (f"Status Code: {result.status_code}")
        
        return result


    def fetch (self, endpoint, body=None):

        fetch_url = self.api_url + endpoint
        if body:
            result = self.fetch_api_post (url=fetch_url, body=body)
        else:
            result = self.fetch_api_get (url=fetch_url)
        return result


    def loop_fetch (self, endpoint, body=None, start=1, page_size=100):

        data = []

        # Mimic a do while loop
        while True:
            batch = self.fetch(endpoint=f"{endpoint}?start={start}&limit={page_size}",body=body)
            if batch.status_code == 200:
                data.extend(batch.json())
                start += page_size
                if len(batch.json()) < page_size:
                    break
            else: 
                if self.debug:
                    print ('Loop failed.')
                break
        return data


    # Specific data

    def fetch_scans(self):

        url = f'/projects/{self.project_id}/scans'

        scans = []
        scans = self.loop_fetch (endpoint=url, start=1, page_size=100)

        self.scans_df = pd.DataFrame(scans)
        self.scan_types = self.scans_df['scan_type'].unique().tolist()


    def fetch_findings(self, scan_type = None):

        if scan_type in self.scan_types:

            url = f'/projects/{self.project_id}/findings/search'
            body = {"scan_type":scan_type.lower()}


            findings = []
            findings = self.loop_fetch (endpoint=url, body=body, start=1, page_size=1000)

            self.findings_df = pd.DataFrame(findings)

        else:
            # Can we get a list of scan types?
            print (f"Scan Type invalid! Use {self.scan_types}")


    #
    # ***** Return Data *****
    #

    def get_scans(self, scan_type=None):

        if scan_type in self.scan_types:
            return self.scans_df[self.scans_df['scan_type'] == scan_type].copy()
        else:
            return self.scans_df.copy()
        

    def get_findings(self):

        return self.findings_df.copy()   
    
    #
    # ***** Export Data *****
    #

    def save_scans_csv(self, scan_type=None, file_name=None):

        if file_name:
            if scan_type in self.scan_types:
                self.scans_df['scan_type'].to_csv(file_name, index=False)
            else:
                self.scans_df.to_csv(file_name, index=False)
            

    def save_findings_csv(self, file_name=None):

        if file_name:
            self.findings_df.to_csv(file_name, index=False)
        