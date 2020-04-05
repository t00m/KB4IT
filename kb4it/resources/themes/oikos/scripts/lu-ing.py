"""
# File: lu-ing.py
# Author: Tomás Vírseda
# License: GPL v3
# Description:  Create a simple CSV file to be used by KB4IT/Oikos theme
                from a detailed ING.LU JSON export
"""

import re
import csv
import sys
import json
import uuid
from datetime import datetime

class ING:
    def get_timestamp(self, adate):
        return adate.strftime("%Y.%m.%d")

    def cleanup_string(self, text):
        new_text = re.sub(" +", " ", text)
        new_text = new_text.strip()
        return new_text

    def get_data(self, filename):
        with open(filename, 'r') as flu:
            data = json.load(flu)
            print ("<-- Read file %s with %d entries successfully" % (filename, len(data)))
        return data

    def analyze(self, data):
        now = self.get_timestamp(datetime.today())
        filename = "oikos-lu-ing-%s.csv" % now.replace('.', '')
        writer = csv.writer(open(filename, 'w'), delimiter=',', quoting=csv.QUOTE_ALL)
        csvheader = ['Id', 'Date', 'Concept', 'Type', 'Category', 'From/To', 'Amount']
        writer.writerow(csvheader)
        for tx in data:
            # ~ tx = data[node]
            op_id = tx['id']
            op_date = tx['operationDate']['value'].replace('-', '.')
            op_text = self.cleanup_string(tx['text'])
            op_amount = tx['amount']['value']
            if op_amount < 0:
                op_type = 'Expense'
            else:
                op_type = 'Income'
            try:
                op_cat = tx['communication']
            except:
                op_cat = ''
            try:
                op_fromto = tx['beneficiaryName']
            except:
                op_fromto = ''
            csvrow = [op_id, op_date, op_text, op_type, op_cat, op_fromto, op_amount]
            writer.writerow(csvrow)
        print("--> File %s saved successfully with %d entries" % (filename, len(data)))


if __name__ == '__main__':
    try:
        jsonfile = sys.argv[1]
        ing = ING()
        data = ing.get_data(jsonfile)
        ing.analyze(data)
    except IndexError as error:
        print ("Usage: python3 lu-ing.py ing_file.json\n")
    except Exception as error:
        print(error)
        raise
