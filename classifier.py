import json
import pandas as pd
import re
import requests
import time
import urllib.parse
import urllib.request

LIBPOSTAL_API_PARSE_PATH = 'http://localhost:4400/parse'

DATA_INPUT_FILENAME = 'input.txt'
DATA_OUTPUT_FILENAME = 'classified.xlsx'

POSTAL_CODE_REGEX = r'\b((([a-zA-Z]{1,3}[-\s]?)?\d{4,8}([-]\d{3})?)|((?=\w*\d)[\w]{3,4}[-\s]?(?=\w*\d)[\w]{3})|(([a-zA-Z]{1,2}[-])?\d{2,3}[-\s]\d{2,3}))\b'

key = r'AIzaSyBBhpByne0olNb3kPIKceo5Q9uAtYH5s_k'


def read_DataFrame_from_file():
    return pd.read_csv(DATA_INPUT_FILENAME, delimiter='\t', keep_default_na=False)


def write_DataFrame_to_excel(df: pd.DataFrame):
    sheet_name = 'Classified'

    with pd.ExcelWriter(DATA_OUTPUT_FILENAME, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        worksheet = writer.sheets[sheet_name]
        # format all data as a table
        worksheet.add_table(0, 0, df.shape[0], df.shape[1] - 1, {
            'columns': [{'header': col_name} for col_name in df.columns],
            'style': 'Table Style Medium 5'
        })
        # Widen the address column
        worksheet.set_column('C:C', 70)

        # Add formatting - red for negative, green - for positive qualification
        redFormat = writer.book.add_format({'bg_color': '#FF0000', 'font_color': '#000000'})
        greenFormat = writer.book.add_format({'bg_color': '#00B050', 'font_color': '#000000'})
        worksheet.conditional_format(0, 0, df.shape[0], df.shape[1] - 1, {'type': 'formula',
                                                                          'criteria': '=$E1=0',
                                                                          'format': redFormat})
        worksheet.conditional_format(0, 0, df.shape[0], df.shape[1] - 1, {'type': 'formula',
                                                                          'criteria': '=$E1=1',
                                                                          'format': greenFormat})


def does_contain_valid_postal_code(input):
    match = re.search(POSTAL_CODE_REGEX, input)
    if match is not None:
        return match.group(0)
    return None


def contains_two_groups_number(input):
    if any(i.isdigit() for i in input):
        return check_group_of_words(input)
    return False


def check_group_of_words(input):
    words = input.split()
    if len(words) - 1 >= 4:
        return True
    return False


def enrich_row_with_address_details(row):
    error_response = [0, None, None, None, None]

    city = None
    post_code = None
    street = None
    house_number = None

    address = row['person_address']
    country = row['person_ctry_code']

    complete = 0

    if not address:
        return error_response

    response = {}

    """if country == 'RU':
        address = treat_russian_address(address)"""

    if contains_two_groups_number(address):
        address = address.replace(',', ', ')
        try:
            unmapped_response = requests.get(LIBPOSTAL_API_PARSE_PATH, params={'address': address}).json()
            response = {entry['label']: entry['value'] for entry in unmapped_response}
        except Exception as e:
            print('Failed to parse address {} | error: {}'.format(address, e))
            return error_response

        city = response['city'] if 'city' in response else None
        post_code = response['postcode'] if 'postcode' in response else None
        street = response['road'] if 'road' in response else None
        house_number = response['house_number'] if 'house_number' in response else None

        if city is not None and street is not None and house_number is not None and post_code is None:
            post_code = does_contain_valid_postal_code(address)

        if city is not None and post_code is None:
            post_code = fix_city_postcode_together(address, city)

        complete = 1 if street and house_number and post_code and city else 0

    return complete, street, house_number, post_code, city


"""def treat_russian_address(input):
    words = input.split(',')
    post = ''
    city = ''
    new_address = ''

    for word in words:
        if len(word) == 6 and word.isnumeric():
            post += word
            city += words[words.index(post) + 1]
            words.remove(city)
            words.remove(post)
            break

    for word in words:
        new_address += word
        new_address += ', '

    new_address += city
    new_address += ', '
    new_address += post

    return new_address"""


def split_input(address):
    address = address.replace(',', ' ')
    address = address.replace(';', ' ')
    address = address.replace(" '", ' ')
    address = address.replace("(", ' ')
    address = address.replace(")", ' ')
    words = address.lower().split()
    return words


def fix_city_postcode_together(address, city):

    words = split_input(address)

    return get_next_before_in_list(words, city)


def get_next_before_in_list(words, city):
    postcode = None
    names = city.lower().split()
    length = len(names)
    new = []

    try:
        if length > 1:
            i = words.index(names[0])
            before = words[i - 1]
            if any(char.isdigit() for char in before):
                return before
            else:
                for idx in range(length):
                    new.append(words[words.index(names[idx])])
                if new == names:  # and (words.index(names[len(names)-1]) + 1) < length:
                    after = words[words.index(names[idx]) + 1]
                    if any(char.isdigit() for char in after):
                        return after
        else:
            # if (words.index(city) - 1) > 0:
            before = words[words.index(city) - 1]
            if any(i.isdigit() for i in before):
                return before

            after = words[words.index(city) + 1]
            if any(i.isdigit() for i in after):
                return after

    except Exception as e:
        print('Failed to find postcode {} | error: {}'.format(words, e))
        return None

    return postcode


def classify_address(dataFrame: pd.DataFrame):
    dataFrame[['complete', 'street', 'house', 'postal_code', 'city']] = \
        dataFrame.apply(enrich_row_with_address_details, axis=1, result_type='expand')
    return dataFrame


def init():
    classified = classify_address(read_DataFrame_from_file())
    write_DataFrame_to_excel(classified)


init()
