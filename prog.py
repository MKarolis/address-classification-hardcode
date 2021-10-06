
import pandas as pd
import re
import requests
import json

DATA_INPUT_FILENAME = 'input.txt'
DATA_OUTPUT_FILENAME = 'classified.xlsx'

POSTAL_CODE_REGEX = r'\b((([a-zA-Z]{1,3}[-\s]?)?\d{4,8}([-]\d{3})?)|((?=\w*\d)[\w]{3,4}[-\s]?(?=\w*\d)[\w]{3})|(([a-zA-Z]{1,2}[-])?\d{2,3}[-\s]\d{2,3}))\b'


def read_DataFrame_from_file():
    return pd.read_csv(DATA_INPUT_FILENAME, delimiter='\t', keep_default_na=False)


def write_DataFrame_to_excel(df: pd.DataFrame):
    sheet_name = 'Classified'

    with pd.ExcelWriter(DATA_OUTPUT_FILENAME, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        worksheet = writer.sheets[sheet_name]
        # format all data as a table
        worksheet.add_table(0, 0, df.shape[0], df.shape[1]-1, {
            'columns': [{'header': col_name} for col_name in df.columns],
            'style': 'Table Style Medium 5'
        })
        # Widen the address column
        worksheet.set_column('C:C', 70)

        # Add formatting - red for negative, green - for positive qualification
        redFormat = writer.book.add_format(
            {'bg_color': '#FF0000', 'font_color': '#000000'})
        greenFormat = writer.book.add_format(
            {'bg_color': '#00B050', 'font_color': '#000000'})
        worksheet.conditional_format(0, 0, df.shape[0], df.shape[1]-1, {'type': 'formula',
                                                                        'criteria': '=$E1=0',
                                                                        'format': redFormat})
        worksheet.conditional_format(0, 0, df.shape[0], df.shape[1]-1, {'type': 'formula',
                                                                        'criteria': '=$E1=1',
                                                                        'format': greenFormat})


def does_contain_valid_postal_code(input):
    match = re.search(POSTAL_CODE_REGEX, input)
    if (match is not None):
        return True
    return False


def does_contain_valid_city_name(input):
    

    return bool([city for city in cities if(city in input)])


def is_valid_address(input):
    # return does_contain_valid_postal_code(input)
    
    return does_contain_valid_city_name(input)


def classify_address(dataFrame: pd.DataFrame):
    dataFrame['complete'] = dataFrame.apply(
        lambda row: 1 if is_valid_address(row['person_address']) else 0, axis=1)

    return dataFrame


if __name__ == '__main__':
    
    cities_url = "https://pkgstore.datahub.io/core/world-cities/world-cities_json/data/5b3dd46ad10990bca47b04b4739a02ba/world-cities_json.json"
    cities_json = json.loads(requests.get(cities_url).content.decode('utf8'))

    # countries = set([city['country'] for city in cities_json])
    cities = set([city['name'] for city in cities_json])
    
    classified = classify_address(read_DataFrame_from_file())
    write_DataFrame_to_excel(classified)

    
    
    
    
    
    
