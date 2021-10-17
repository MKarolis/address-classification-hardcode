import pandas as pd
import re
import requests
import time

LIBPOSTAL_API_PARSE_PATH = 'http://localhost:4400/parse'

DATA_INPUT_FILENAME = 'input.txt'
DATA_OUTPUT_FILENAME = 'classified.xlsx'

POSTAL_CODE_REGEX = r'\b(?<!\-)((([a-zA-Z]{1,3}[-\s]?)?\d{4,8}([-]\d{3})?)|((?=\w*\d)[\w]{3,4}[-\s]?(?=\w*\d)[\w]{3})|(([a-zA-Z]{1,2}[-])?\d{2,3}[-\s]\d{2,3}))\b(?!-)'


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


def extract_postal_code(input):
    match = re.search(POSTAL_CODE_REGEX, input)
    if (match is not None):
        return match.group(0)
    return None


def does_contain_valid_postal_code(input):
    match = re.search(POSTAL_CODE_REGEX, input)
    if (match is not None):
        return True
    return False


def count_words(input):
    return len(re.findall(r'[^\s,]+', input))


def collect_property_list(property, array):
    return list(map(lambda row: row['value'] , filter(lambda row: row['label'] == property , array)))


def get_normalized_house_number_and_postal(house_numbers):
    house_num = None
    postal = None

    for number in house_numbers:
        if house_num and postal:
            break
        possible_postal = extract_postal_code(number)

        if not postal and possible_postal:
            postal = possible_postal
            number = number.replace(possible_postal, '').strip()

        if not house_num and number and len(number) > 0:
            house_num = number


    return house_num, postal


def enrich_row_with_address_details(row):
    error_response = [0, None, None, None, None]

    address = row['person_address']
    country = row['person_ctry_code']

    if not address:
        return error_response
    
    address = address.replace(',', ', ')
    address = address.replace(' - ', '-')

    if len(address.split()) < 3:
        return error_response

    address = validate_asian_address_before_api(address, country)

    try:
        unmapped_response = requests.get(LIBPOSTAL_API_PARSE_PATH, params={ 'address': address }).json()
    except Exception as e:
        print('Failed to parse address {} | error: {}'.format(address, e))
        return error_response

    roads = collect_property_list('road', unmapped_response)
    house_numbers = collect_property_list('house_number', unmapped_response)
    post_codes = collect_property_list('postcode', unmapped_response)
    cities = collect_property_list('city', unmapped_response)

    street = roads[0] if len(roads) > 0 else None
    house_number = house_numbers[0] if len(house_numbers) > 0 else None
    post_code = post_codes[0] if len(post_codes) > 0 else None
    city = cities[0] if len(cities) > 0 else None

    if not post_code:
        tmp_house_num, tmp_postal = get_normalized_house_number_and_postal(house_numbers)
        if tmp_house_num and tmp_postal:
            house_number = tmp_house_num
            post_code = tmp_postal
            if street and house_number and post_code and city:
                print('NORMALIZED POSTAL CODE FROM HOUSE NUMBER FOR ', address) 

    
    complete = 1 if (street or country =='JP' or country == 'KR' or country == 'CN') and house_number and post_code and city else 0

    return complete, street, house_number, post_code, city


def validate_asian_postal_code_before_api(address, number):

    japanese_postal_code = re.findall(fr'\b\d{{{number}}}\b', address)
    
    if japanese_postal_code:
      
        old_postal_code = japanese_postal_code[0]
        new_postal_code = old_postal_code[:3] + "-" + old_postal_code[3:]
        return address.replace(old_postal_code, new_postal_code)
        
        print(f'address: {address}, before: {old_postal_code}, after: {new_postal_code}')

def validate_asian_address_before_api(address, country):
    
    if country == 'JP': return validate_asian_postal_code_before_api(address, 7)
    elif country == 'CN' or country == 'KR': return validate_asian_postal_code_before_api(address, 6)
    else: return address


def classify_address(dataFrame: pd.DataFrame):
    dataFrame[['complete', 'street', 'house', 'postal_code', 'city']]=dataFrame.apply(
        enrich_row_with_address_details, axis=1, result_type='expand')
    return dataFrame



if __name__ == '__main__':

    start=time.time()

    classified=classify_address(read_DataFrame_from_file())
    write_DataFrame_to_excel(classified)

    end=time.time()

    print(f"\nTime in seconds: {end - start}")
