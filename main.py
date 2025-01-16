import re
import csv

from requests import get
from rich.console import Console
from rich.table import Table

api_username = "rinyre+voip@gmail.com"
api_password = "WLEBEErq9W7v"

## App below

api_root = "https://voip.ms/api/v1/rest.php"

noyes = ["N","Y"]

def api_action(action: str,**kwargs):
    params = {
        "content_type": "json",
        "api_username": api_username,
        "api_password": api_password,
        "method": action
    }
    if len(kwargs) > 0:
        params.update(kwargs)
    r = get(api_root,params=params)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(r.url,r.request.body)

def strToT9(string: str):
    t9_str_list = []
    t9_tuple = ("","","2ABC","3DEF","4GHI","5JKL","6MNO","7PQRS","8TUV","9WXYZ")
    for letter in string:
        for key in t9_tuple[2:]:
            if letter.upper() in key:
                t9_str_list.append(t9_tuple.index(key))
                break
    t9_str = "".join([str(x) for x in t9_str_list])
    if len(t9_str) == len(string):
        return t9_str
    else:
        raise TypeError("Search input must be alphanumeric only")

def add_row(table,did,search_string,search_term):
    start = did['did'].index(search_string)
    end = start + len(search_string)
    highlight_number = f"{did['did'][0:start]}[b green3]{did['did'][start:end]}[/b green3]{did['did'][end:]}"
    highlight_search = f"{did['did'][0:start]}[b green3]{search_term.upper()}[/b green3]{did['did'][end:]}"
    table.add_row(
        did['state'],
        f"{highlight_number}\n{highlight_search}",
        f"${did['perminute_setup']} / ${did['flat_setup']}",
        f"${did['perminute_monthly']} / ${did['flat_monthly']}",
        f"${did['perminute_minute']} / ${did['flat_minute']}",
        noyes[did['sms']]
    )

def main():
    console = Console()
    states = []
    results = []
    search_term = ""
    term_check_bad = lambda x: re.match(r'[^a-zA-Z0-9]',x) or len(x) > 10
    while term_check_bad(search_term) or len(search_term) < 3:
        search_term = console.input("Primary search> ")
        if term_check_bad(search_term):
            console.print("Invalid search term, must be 3-10 alphanumeric characters")
    optional_search = console.input("Optional sub-search> ")
    if optional_search != "":
        while term_check_bad(optional_search) or search_term.upper() not in optional_search.upper() and search_term != "":
            console.print("Invalid search term, must be no longer than 10 alphanumeric characters and contain original search term")
            optional_search = console.input("Optional sub-search> ")
    if optional_search == "":
        console.print("Skipping optional sub-search")
    try:
        response = api_action("getStates")
        states.extend(response['states'])
    except Exception as e:
        console.print_exception()
    search_string = strToT9(search_term)
    console.print(f"Iterating states for '[b]{search_term.upper()}[/b]' ({search_string})")
    for state in states:
        console.print(f"Searching {state['description']}...")
        search_response: dict[str,str|list[dict[str,str|int]]] = api_action("searchDIDsUSA",state=state['state'],type="contains",query=search_string)
        if search_response['status'] == "success":
            results.extend(search_response['dids'])
            console.print(f"     Found [b]{len(search_response['dids'])}[/b] numbers")
            # for did in search_response.dids:
            #     start = did['did'].index(search_string)
            #     end = start + len(search_string)
            #     console.print(f"     Found: {did['did'][0:start]}[b green3]{did['did'][start:end]}[/b green3]{did['did'][end:]}")
        else:
            # console.print("     Nothing found.")
            continue
    if len(results) > 0:
        table = Table(show_header=True,header_style="bold red",show_lines=True)
        for column in ["State","Number","Setup","Monthly","Minute","SMS?"]:
            table.add_column(column)
        filename = f"{search_term}_results.csv"
        with open(filename,"w",newline="") as f:
            csvfile = csv.writer(f)
            columns = ["state","did","subsearch","sms"]
            if not optional_search:
                columns.remove("subsearch")
            csvfile.writerow(columns)
            for did in results:
                if optional_search:
                    subsearch_string = strToT9(optional_search) 
                    has_subsearch = subsearch_string in did['did']
                    csvfile.writerow([did['state'],did['did'],noyes[int(has_subsearch)],noyes[did['sms']]])
                    if has_subsearch:
                        add_row(table,did,subsearch_string,optional_search)
                else:
                    csvfile.writerow([did['state'],did['did'],noyes[did['sms']]])
                add_row(table,did,search_string,search_term)

        console.print(table)
        console.print(f"Wrote results to [b]{filename}[/b]")
    else:
        console.print("Did not find any results.")

if __name__ == "__main__":
    main()