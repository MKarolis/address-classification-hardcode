import pandas as pd
import re

DATA_INPUT_FILENAME = 'input.txt'
DATA_OUTPUT_FILENAME = 'classified.xlsx'

POSTAL_CODE_REGEX = r'\b((([a-zA-Z]{1,3}[-\s]?)?\d{4,8}([-]\d{3})?)|((?=\w*\d)[\w]{3,4}[-\s]?(?=\w*\d)[\w]{3})|(([a-zA-Z]{1,2}[-])?\d{2,3}[-\s]\d{2,3}))\b'


def read_DataFrame_from_file():
    return pd.read_csv(DATA_INPUT_FILENAME, delimiter='\t', keep_default_na=False)


def write_DataFrame_to_excel(df: pd.DataFrame):
    sheet_name = 'Cllassified'

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
        return True
    return False


def contains_two_groups_number(input):
    new = ""
    control = False
    count = 0

    for elem in input:
        if elem.isdigit():
            new += elem
            control = True
        if elem == '-' and control:
            new += elem
        if control and not elem.isdigit() and elem != '-':
            count += 1
            new += 'a'
            control = False

    # print(new)

    if count == 1:
        if new[-1].isalpha():
            # print("last: " + new[-1])
            print("Eliminated at 2")
            return False
        if new[-1].isdigit():
            check_street(input)
            # return True

    if count > 1:
        check_street(input)
        # return True

    else:
        print("Eliminated at 2-B")
        return False


def check_group_of_words(input):
    a = sum(map(input.count, [',']))
    b = sum(map(input.count, [' ']))
    c = sum(map(input.count, [", "]))
    d = sum(map(input.count, [" , "]))

    divisions = b - c - d + a
    # print(divisions)

    if divisions >= 3:
        return contains_two_groups_number(input)
    else:
        print("Eliminated at 1")
        return False


def check_street(input):
    street = ['Street', 'straat', 'Avenue', 'Rua', 'Avenida', 'Road']
    verif = True

    for elem in street:
        if input.find(elem) > -1:
            print('Word: ' + elem)
            print('3a verificacao true')
            verif = True

    return verif


def is_valid_address(input):
    # res = does_contain_valid_postal_code(input)
    # res = contains_two_groups_number(input)
    res = check_group_of_words(input)
    print(input)
    print(res)
    return res


def classify_address(dataFrame: pd.DataFrame):
    dataFrame['complete'] = dataFrame.apply(lambda row: 1 if is_valid_address(row['person_address']) else 0, axis=1)

    return dataFrame


def init():
    classified = classify_address(read_DataFrame_from_file())
    write_DataFrame_to_excel(classified)


init()
