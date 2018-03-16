# -*- coding: utf-8 -*-
"""
 DatabaseCreation.utils.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions for database creation
"""
from cdesnowball.doc import Document
from cdesnowball.scrape import Selector
from cdesnowball.scrape.pub.acs import AcsHtmlDocument
from cdesnowball.scrape.pub.rsc import RscHtmlDocument
from cdesnowball.scrape.pub.elsevier import ElsevierHtmlDocument, \
    ElsevierXmlDocument
from cdesnowball.scrape.pub.springer import SpringerHtmlDocument
import re
import os
import sys
import traceback


UNICODE_PREDICATES = ('\u02dc',
                      '\u007e',
                      '\u0334',
                      '\u0336',
                      '\u223d',
                      '\u223c',
                      '\uff5e',
                      '\u2245',
                      '\u2246',
                      '\u2a85',
                      '\u2a86',
                      '\u2265',
                      '\u2267',
                      '\u226b',
                      '\u2273',
                      '\u2264',
                      '\u2266',
                      '\u226a',
                      '\u2272')
UNICODE_DEGREES_CELSIUS = ['°C', 'C', '\u00b0C', '\u2103']
UNICODE_DEGREES_FAHRENHEIT = ['°F', 'F', '\u00b0F', '\u2109']


def get_document_info(file):
    """
    Scrape document information using ChemDataExtractor Scrapers
    :param file: file path to target article
    :type file: str
    :return: list of dicts containing the document information
    """

    if file.endswith('.html'):
        file_type = 'html'
    elif file.endswith('.xml'):
        file_type = 'xml'
    else:
        return
    print("file type", file_type)

    f = open(file, 'rb').read()

    sel = Selector.from_text(f)
    # Determine publishers, use the RSC scraper by default
    publisher = detect_publisher(f)
    if publisher == 'acs':
        document_info = AcsHtmlDocument(sel)
    elif publisher == 'rsc':
        document_info = RscHtmlDocument(sel)
    elif publisher == 'elsevier' and file_type == 'html':
        document_info = ElsevierHtmlDocument(sel)
    elif publisher == 'elsevier' and file_type == 'xml':
        document_info = ElsevierXmlDocument(sel)
    elif publisher == 'springer' and file_type == 'html':
        document_info = SpringerHtmlDocument(sel)
    else:
        print('Unknown Journal for file' + file + 'using RSC HTML formatting by default')
        document_info = RscHtmlDocument(sel)

    return document_info


def get_chemical_records(file):
    """
    get chemical records extracted from CDE-snowball, removing records that do not contain compound names
    :param file: path to file
    :type file: str
    :return: ChemDataExtractor records in list of dict format
    """
    f = open(file, 'rb')
    try:
        doc = Document.from_file(f)
        recs = doc.records
        output_recs = []
        print("Removing blank records")
        for compound in recs:
            if compound.names is not None:
                output_recs.append(compound)

        f.close()
        return output_recs
    except Exception as e:
        print('File ' + file + ' could not be read. ' + 'Error: ' + str(e))
        traceback.print_exc(file=sys.stdout)
        f.close()
    return


def normalise_temperature(input_temperature):
    """ Convert units of a temperature measurement to Kelvin
    :param input_temperature: The temperature to be normalised in Degrees
    Celsius
    :type input_temperature: ChemDataExtractor Record
    :returns: Normalised temperature in Kelvin
    """
    value = str(input_temperature.value)
    units = input_temperature.units

    if units is None:
        return value, units
    elif units == 'K' or units == 'K.' or units == 'θ':
        return value, units
    if units == 'mK' or units == 'mK.':
        return str(float(value)/1000.0), 'K'
    elif value.startswith(UNICODE_PREDICATES):
        predicate = value[0]
        temperature = value[1:]
        if any(units == x for x in UNICODE_DEGREES_CELSIUS):
            temperature_flt = float(temperature) + 273
            return predicate + str(temperature_flt), 'K'
        elif any(units == x for x in UNICODE_DEGREES_FAHRENHEIT):
            temperature_flt = (5.0 / 9.0) * (float(temperature) - 32) + 273
            return predicate + str(temperature_flt), 'K'
        else:
            print('Something went wrong', value, units)
            return None, None
    elif re.search(r'[\d.]+[\-\-­᠆‐‑⁃﹣–－−˗][\d.]+', value) is not None:
        lower_temperature = re.split(r'[\-\-\–­᠆‐‑⁃﹣－−˗]', value)[0]
        upper_temperature = re.split(r'[\-\-\–­᠆‐‑⁃﹣－−˗]', value)[1]
        if any(units == x for x in UNICODE_DEGREES_CELSIUS):
            lower_temperature_flt = float(lower_temperature) + 273
            upper_temperature_flt = float(upper_temperature) + 273
            return str(lower_temperature_flt) + '-' + str(upper_temperature_flt), 'K'
        elif any(units == x for x in UNICODE_DEGREES_FAHRENHEIT):
            lower_temperature_flt = (5.0 / 9.0) * (float(lower_temperature) - 32) + 273
            upper_temperature_flt = (5.0 / 9.0) * (float(upper_temperature) - 32) + 273
            return str(lower_temperature_flt) + '-' + str(upper_temperature_flt), 'K'
        else:
            print('Something went wrong', value, units)
            return None, None
    elif re.search(r'[\d.]+[±∓⨤⨦][\d.]+', value) is not None:
        temperature = re.split(r'[±∓⨤⨦]', value)[0]
        error = re.split(r'[±∓⨤⨦]', value)[1]
        if any(units == x for x in UNICODE_DEGREES_CELSIUS):
            temperature_flt = float(temperature) + 273
            return str(temperature_flt) + '±' + error, 'K'
        elif any(units == x for x in UNICODE_DEGREES_FAHRENHEIT):
            lower_temp_fahren = float(temperature) - float(error)
            upper_temperature_fahren = float(temperature) + float(error)
            temperature_flt_kelvin = (5.0 / 9.0) * (float(temperature) - 32) + 273
            lower_temperature_flt_kelvin = (5.0 / 9.0) * (float(lower_temp_fahren) - 32) + 273
            upper_temperature_flt_kelvin = (5.0 / 9.0) * (float(upper_temperature_fahren) - 32) + 273
            error_kelvin = (1.0 / 2.0) * (upper_temperature_flt_kelvin - lower_temperature_flt_kelvin)
            return str(temperature_flt_kelvin) + '±' + str(error_kelvin), 'K'
        else:
            print('Something went wrong', value, units)
            return None, None
    elif re.match(r'^[\-\-­᠆‐‑⁃﹣－−˗]?[\d.]+$', value):
        temperature = value
        if any(units == x for x in UNICODE_DEGREES_CELSIUS):
            temperature_flt = float(temperature) + 273
            return str(temperature_flt), 'K'
        elif any(units == x for x in UNICODE_DEGREES_FAHRENHEIT):
            temperature_flt = (5.0 / 9.0) * (float(temperature) - 32) + 273
            return str(temperature_flt), 'K'
        else:
            print('Could not normalise:', value, units)
            return None, None
    else:
        print('UNKOWN FORMAT', value, units)
        return None, None


def exists(file):
    """ Check if a specified file exists"""
    if not os.path.exists(file):
        return False
    else:
        return True


def detect_publisher(fstring):
    """ Detect the publisher of a html file by searching for unique strings
    :param fstring: document HTML or XML text
    :type: byte string
    :returns: publisher name as a unique string
    """
    if b'<meta name="dc.Identifier" scheme="doi" content="10.1021/' in fstring:
        return 'acs'
    elif b'content="10.1039/' in fstring:
        return 'rsc'
    elif b'<link rel="canonical" href="http://www.sciencedirect.com/' in fstring:
        return 'elsevier'
    elif b'full-text-retrieval-response' in fstring:
        return 'elsevier'
    elif b'<meta content="10.1007/' in fstring or b'<meta content="https://link.springer.com' in fstring:
        return 'springer'
    else:
        return None