# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
from collections import OrderedDict

import regex as re
from ruamel.yaml import RoundTripLoader

from utils import AVOID_LANGUAGES, combine_dicts, language_from_filename

cldr_date_directory = '../dateparser_data/cldr_language_data/date_translation_data/'
cldr_numeral_directory = '../dateparser_data/cldr_language_data/numeral_translation_data/'
supplementary_directory = '../dateparser_data/supplementary_language_data/'
supplementary_date_directory = '../dateparser_data/supplementary_language_data/date_translation_data/'
translation_data_directory = '../dateparser/data/'
date_translation_directory = '../dateparser/data/date_translation_data/'
numeral_translation_directory = '../dateparser/data/numeral_translation_data/'

os.chdir(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger('data_scripts')

cldr_languages = set([language_from_filename(filename) for filename
                      in os.listdir(cldr_date_directory)]) - AVOID_LANGUAGES
supplementary_languages = set([language_from_filename(filename) for filename
                               in os.listdir(supplementary_date_directory)])
all_languages = cldr_languages.union(supplementary_languages)

cldr_numeral_languages = [language_from_filename(filename) for filename
                          in os.listdir(cldr_numeral_directory)]

RELATIVE_PATTERN = re.compile(r'\{0\}')
encoding_comment = "# -*- coding: utf-8 -*-\n"


def _modify_relative_data(relative_data):
    modified_relative_data = OrderedDict()
    for key, value in relative_data.items():
        for i, string in enumerate(value):
            string = RELATIVE_PATTERN.sub(r'(\\d+)', string)
            value[i] = string
        modified_relative_data[key] = value


def _modify_data(language_data):
    relative_data = language_data.get("relative-type-regex", {})
    _modify_relative_data(relative_data)
    locale_specific_data = language_data.get("locale_specific", {})
    for _, info in locale_specific_data.items():
        locale_relative_data = info.get("relative-type-regex", {})
        _modify_relative_data(locale_relative_data)


def _get_complete_date_translation_data(language):
    cldr_data = {}
    supplementary_data = {}
    if language in cldr_languages:
        with open(cldr_date_directory + language + '.json') as f:
            cldr_data = json.load(f, object_pairs_hook=OrderedDict)
    if language in supplementary_languages:
        with open(supplementary_date_directory + language + '.yaml') as g:
            supplementary_data = OrderedDict(RoundTripLoader(g).get_data())
    complete_data = combine_dicts(cldr_data, supplementary_data)
    if 'name' not in complete_data:
        complete_data['name'] = language
    return complete_data


def main():
    if not os.path.isdir(translation_data_directory):
        os.mkdir(translation_data_directory)
    if os.path.isdir(date_translation_directory):
        shutil.rmtree(date_translation_directory)
    os.mkdir(date_translation_directory)
    with open(supplementary_directory + 'base_data.yaml') as f:
        base_data = RoundTripLoader(f).get_data()

    for language in all_languages:
        date_translation_data = _get_complete_date_translation_data(language)
        date_translation_data = combine_dicts(date_translation_data, base_data)
        _modify_data(date_translation_data)
        translation_data = json.dumps(date_translation_data, indent=4, separators=(',', ': '),
                                      ensure_ascii=False)
        out_text = (encoding_comment + 'info = ' + translation_data).encode('utf-8')
        with open(date_translation_directory + language + '.py', 'wb') as out:
            out.write(out_text)

    if os.path.isdir(numeral_translation_directory):
        shutil.rmtree(numeral_translation_directory)
    os.mkdir(numeral_translation_directory)
    for language in cldr_numeral_languages:
        with open(cldr_numeral_directory + language + '.json') as f:
            numeral_translation_data = json.load(f, object_pairs_hook=OrderedDict)
        numeral_data = json.dumps(numeral_translation_data, indent=4, separators=(',', ': '),
                                  ensure_ascii=False)
        out_text = (encoding_comment + 'info = ' + numeral_data).encode('utf-8')
        with open(numeral_translation_directory + language + '.py', 'wb') as out:
            out.write(out_text)

    init_text = '\n'.join(
        ["from dateparser.data import date_translation_data, numeral_translation_data",
         "from .languages_info import language_order, language_locale_dict"]
    )
    with open(translation_data_directory + '__init__.py', 'w') as out:
        out.write(encoding_comment + init_text)

    with open(date_translation_directory + '__init__.py', 'w') as out:
        out.write(encoding_comment)

    with open(numeral_translation_directory + '__init__.py', 'w') as out:
        out.write(encoding_comment)


if __name__ == '__main__':
    main()