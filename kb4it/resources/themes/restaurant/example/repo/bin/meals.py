import os
import csv
import sys
import json
import requests
from datetime import datetime
from string import Template


TPL_MENU = """= $title

:Lunch:             $lunch
:Dinner:            $dinner
:Ingredient:        $ingredients
:Served:            $title

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== Notes

$notes

"""

def get_source_dir():
    module = os.path.dirname(__file__)
    config_file = os.path.join(module, '..', 'config/repo.json')
    with open(config_file, 'r') as fc:
        config = json.load(fc)
        return config['source']

def get_sheet(url, outDir, outFile):
    response = requests.get(url)

    # Download sheet
    if response.status_code == 200:
        filepath = os.path.join(outDir, outFile)
        tmp_filepath = os.path.join(outDir, f'tmp_{outFile}')
        with open(tmp_filepath, 'wb') as f:
            f.write(response.content)
            # ~ print(f'Temporay CSV file saved to: {tmp_filepath}')

        # Save CSV with quotes and use semicolon as delimiter
        with open(tmp_filepath, 'r') as csv_in, \
             open(filepath, 'w', newline='') as csv_out:
            reader = csv.reader(csv_in)
            writer = csv.writer(csv_out, delimiter=';')
                                # ~ quotechar='"',
                                # ~ quoting=csv.QUOTE_ALL)
            for row in reader:
                writer.writerow(row)
        # ~ print(f'Final CSV file saved to: {filepath}')
    else:
        print(f'Error downloading Google Sheet: {response.status_code}')
        filepath = None
    return filepath


source_dir = get_source_dir()
url_meals = 'https://docs.google.com/spreadsheets/d/16rx5NVDmyBGXl3L0Se1iPoUAT5mF_3GqOSVAUYJbCaE/export?format=csv&gid=0'
url_ingredients = 'https://docs.google.com/spreadsheets/d/16rx5NVDmyBGXl3L0Se1iPoUAT5mF_3GqOSVAUYJbCaE/export?format=csv&gid=298692532'

data_dir = '../data/'
os.makedirs(data_dir, exist_ok = True)
fmeals = get_sheet(url_meals, data_dir, "meals.csv")
fingredients = get_sheet(url_ingredients, data_dir, "ingredients.csv")
print(f'Meals: {fmeals}')
print(f'Ingredients: {fingredients}')
# ~ fmeals = '/home/t00m/Documents/restaurant/data/meals.csv'
# ~ fingredients = '/home/t00m/Documents/restaurant/data/ingredients.csv'

dingredients = {}
dingredients = {}

with open(fingredients, 'r') as csv_ing:
    lines = csv_ing.readlines()
    n = 0
    for line in lines:
        if n > 0:
            row = line.split(';')
            meals = row[0]
            ingredients = row[1]

            for meal in meals.split(','):
                try:
                    dingredients[meal]
                except:
                    dingredients[meal] = [ingredient.strip() for ingredient in ingredients.split(',')]

                try:
                    dingredients[meal]
                except:
                    dingredients[meal] = [ingredient.strip() for ingredient in ingredients.split(',')]

        n += 1


with open(fmeals, 'r') as csv_meals:
    lines = csv_meals.readlines()
    menu = Template(TPL_MENU)
    n = 0
    for line in lines:
        if n > 0:
            row = line.split(';')
            try:
                sdate = f'{row[0]}'
            except:
                continue

            try:
                lunch = f'{row[1]}'
                for meal in lunch.split(','):
                    ingredients = ''
                    singredients = set()
                    lingredients = ''
                    meal = meal.strip()
                    if len(meal) == 0:
                        continue
                    try:
                        ingredients = dingredients[meal]
                    except Exception as error:
                        # ~ print(f"No ingredients found for {meal}")
                        lingredients = []
                    for ingredient in ingredients:
                        singredients.add(ingredient)
                    lingredients = ', '.join(list(singredients))
                    print(f"Ingredients for '{meal}: {lingredients}")
            except Exception as error:
                raise
                lunch = ''
            have_lunch = len(lunch) > 0

            try:
                dinner = f'{row[2]}'
            except:
                dinner = ''
            have_dinner = len(dinner) > 0

            try:
                notes = f'{row[3]}'
            except:
                notes = ''

            if have_lunch and have_dinner:
                td = datetime.strptime(sdate, "%d/%m/%Y")
                filename = td.strftime("%Y%m%d.adoc")
                source_file = os.path.join(source_dir, filename)
                with open(source_file, 'w') as fmenu:
                    fmenu.write(menu.substitute(title=sdate, lunch=lunch, dinner=dinner, ingredients=lingredients, notes=notes))
        n += 1
