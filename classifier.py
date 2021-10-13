import pandas as pd
import re
import requests
import time

LIBPOSTAL_API_PARSE_PATH = 'http://localhost:4400/parse'

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


def enrich_row_with_address_details(row):

    error_response = [0, None, None, None, None]

    address = row['person_address']

    if not address:
        return error_response

    if len(address) < 30:
        return error_response

    if address == '6-29, Nishiki 3-chome Naka-ku, Nagoya-shi,,Aichi 460-8625':
        print('hello')

    address = address.replace(',,', ',' )
    address = address.replace(', ', ',')
    address = address.replace(',', ', ')
    
    response = {}
    try:
        unmapped_response = requests.get(LIBPOSTAL_API_PARSE_PATH, params={
                                         'address': address}).json()
        response = {entry['label']: entry['value']
                    for entry in unmapped_response}
    except Exception as e:
        print('Failed to parse address {} | error: {}'.format(address, e))
        return error_response

    street = response['road'] if 'road' in response else None
    house_number = response['house_number'] if 'house_number' in response else None
    post_code = response['postcode'] if 'postcode' in response else None
    city = response['city'] if 'city' in response else None

    if city and post_code and not street and not house_number:
        parse_result = parse_street_and_number_with_known_postalcode_and_city(address, city, post_code)
        street = parse_result[0]
        house_number = parse_result[1]

    complete = 1 if street and house_number and post_code and city else 0

    return complete, street, house_number, post_code, city


def parse_street_and_number_with_known_postalcode_and_city(address, city, post_code):

    print('\nfirst removing city and postal code')

    temp_address = address.lower()
    temp_address = temp_address.replace(city, '')
    temp_address = temp_address.replace(post_code, '')
    temp_address = ' '.join(temp_address.split())
    temp_address = temp_address.replace(' , ', ' ')
    print(temp_address)

    print('\nsecond split by comma')

    splitted_address = temp_address.split(", ")
    print(splitted_address)

    print('\nthird check the one part with a street and number')

    for part in splitted_address:

        ocurrences = any(chr.isdigit() for chr in part)

        if ocurrences and not part.isdigit():
            print(part)
            street_and_number = part
            break

    print('\nfourth split number from text')

    # temp = re.compile('([a-zA-Z]+)\s+([0-9]+)')
    # splitted_street_and_number = temp.match(street_and_number)

    # splitted_street_and_number = [substring for substring in street_and_number.split() if substring.isdigit()]

    splitted_street_and_number = re.split(
        r'\s+(?=\d)|(?<=\d)\s+', street_and_number)

    print(splitted_street_and_number)

    print('\nFifth assign street to number')
    street = [
        chunk for chunk in splitted_street_and_number if not any(chr.isdigit() for chr in chunk)][0]
    house_number = [
        chunk for chunk in splitted_street_and_number if any(chr.isdigit() for chr in chunk)][0]

    print(f'Street: {street}')
    print(f'Number: {house_number}')

    return [street, house_number]


def classify_address(dataFrame: pd.DataFrame):
    dataFrame[['complete', 'street', 'house', 'postal_code', 'city']] = dataFrame.apply(
        enrich_row_with_address_details, axis=1, result_type='expand')
    return dataFrame


if __name__ == '__main__':

    start = time.time()

    classified = classify_address(read_DataFrame_from_file())
    # write_DataFrame_to_excel(classified)

    end = time.time()
    print(f"\nTempo em segundos: {end - start}")
