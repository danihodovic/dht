import json
import subprocess

from .cmd import ledger


@ledger.command()
def detect_duplicates():
    result = subprocess.run(
        "hledger print -O json", shell=True, check=True, stdout=subprocess.PIPE
    )
    data = json.loads(result.stdout)
    entries = []
    duplicates = []

    for item in data:
        hashed = f'{item["tdate"]} | {item["tcomment"]=} | {item["tdescription"]=}'
        for idx, posting in enumerate(item["tpostings"]):
            if "aquantity" in posting:
                # pylint: disable=line-too-long
                hashed = f"{hashed} | [{idx}] {posting['aquantity']['decimalMantissa']} {posting['acommodity']}"

        if hashed in entries:
            print("Duplicate found: ", hashed, item["tdescription"])
            duplicates.append(hashed)
        else:
            entries.append(hashed)

    print(f"Total number of duplicates: {len(duplicates)}")
