# -*- coding: utf-8 -*-
"""
 Database.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

XLSX database generator for properties extracted by chemdataextractor

:copyright: Copyright 2017 by Callum Court.
:license: MIT, see LICENSE file for more details.
"""
import os
from chemdataextractor.doc import Document
from chemdataextractor.scrape import Selector
from chemdataextractor.scrape.pub.acs import AcsHtmlDocument
from chemdataextractor.scrape.pub.rsc import RscHtmlDocument
from chemdataextractor.scrape.pub.elsevier import ElsevierHtmlDocument, ElsevierXmlDocument
from chemdataextractor.scrape.pub.springer import SpringerHtmlDocument
from abc import abstractmethod
import re
from pymongo import MongoClient
import traceback
import sys


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


def normalise_temperature(nt):
    """ Convert units of a Neel temperature measurement to Kelvin """
    value = str(nt.value)
    units = nt.units

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
            print('Something went wrong', value, units)
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
        """ Detect the publisher of a html file by searching for unique strings """
        if b'<meta name="dc.Identifier" scheme="doi" content="10.1021/' in fstring:
            return 'acs', 'html'
        elif b'content="10.1039/' in fstring:
            return 'rsc', 'html'
        elif b'<link rel="canonical" href="http://www.sciencedirect.com/' in fstring:
            return 'elsevier', 'html'
        elif b'full-text-retrieval-response' in fstring:
            return 'elsevier', 'xml'
        elif b'<meta content="10.1007/' in fstring or b'<meta content="https://link.springer.com' in fstring:
            return 'springer', 'html'
        return None, None


class BaseProperty:
    """ Base class for all types of property Néel temperature, melting point etc"""

    def __init__(self):
        pass

    @abstractmethod
    def from_doc(self, d):
        return


class Doc:
    """ Document object containing all chemical records from ChemDataExtractor and document information
        such as journal, title etc."""

    def __init__(self):
        self.file_location = []
        self.chemical_records = []
        self.document_info = None
        self.journal = []

    def scrape_chemical_records(self, file):
        """ Get the chemical records using ChemDataExtractor Document and snowball"""
        f = open(file, 'rb')
        try:
            doc = Document.from_file(f)
            self.chemical_records = doc.records
        except Exception as e:
            print('File ' + file + ' could not be read. ' + 'Error: ' + str(e))
            traceback.print_exc(file=sys.stdout)
        f.close()
        return

    def scrape_document_info(self, file):
        """ Scrape document information using ChemDataExtractor Scrapers """
        f = open(file, 'rb').read()
        sel = Selector.from_text(f)
        # Determine which journal the document is from and file type, use the RSC scraper by default
        self.journal, file_type = detect_publisher(f)
        if self.journal == 'acs':
            self.document_info = AcsHtmlDocument(sel)
        elif self.journal == 'rsc':
            self.document_info = RscHtmlDocument(sel)
        elif self.journal == 'elsevier' and file_type == 'html':
            self.document_info = ElsevierHtmlDocument(sel)
        elif self.journal == 'elsevier' and file_type == 'xml':
            self.document_info = ElsevierXmlDocument(sel)
        elif self.journal == 'springer' and file_type == 'html':
            self.document_info = SpringerHtmlDocument(sel)
        else:
            print('Unknown Journal for file' + file + 'using RSC HTML formatting by default')
            self.document_info = RscHtmlDocument(sel)

        return

    def from_file(self, file):
        """ Create Document data object from html file """
        if not exists(file):
            return FileExistsError
        else:
            self.file_location = file
            self.scrape_chemical_records(file)
            self.scrape_document_info(file)

        return self


class NeelTemperatureData(BaseProperty):
    """ Néel temperature property data"""

    def __init__(self):
        super(NeelTemperatureData, self).__init__()

    def from_doc(self, d):
        """ Get all Néel temperature data from the document to create database entries,
            Normalise temperatures to Kelvin """
        data_records = []
        for c in d.chemical_records:
            if c.neel_temperatures:
                for nt in c.neel_temperatures:
                    try:
                        normed_value, normed_units = normalise_temperature(nt)
                    except ValueError as e:
                        print(e)
                        normed_value, normed_units = None, None

                    entry = {'Type': 'Néel',
                             'Names': c.names,
                             'Extracted Value': nt.value,
                             'Extracted Units': nt.units,
                             'Normalised Value': normed_value,
                             'Normalised Units': normed_units,
                             'Confidence': nt.confidence,
                             'Title': d.document_info.title,
                             'Authors': d.document_info.authors,
                             'DOI': d.document_info.doi,
                             'Journal': d.document_info.journal
                             }

                    data_records.append(entry)
        return data_records


class CurieTemperatureData(BaseProperty):
    """ Néel temperature property data"""

    def __init__(self):
        super(CurieTemperatureData, self).__init__()

    def from_doc(self, d):
        """ Get all Curie temperature data from the document to create database entries,
            Normalise temperatures to Kelvin """
        data_records = []
        for c in d.chemical_records:
            if c.curie_temperatures:
                for ct in c.curie_temperatures:
                    try:
                        normed_value, normed_units = normalise_temperature(ct)
                    except ValueError as e:
                        print(e)
                        normed_value, normed_units = None, None
                    entry = {'Type': 'Curie',
                             'Names': c.names,
                             'Extracted Value': ct.value,
                             'Extracted Units': ct.units,
                             'Normalised Value': normed_value,
                             'Normalised Units': normed_units,
                             'Confidence': ct.confidence,
                             'Title': d.document_info.title,
                             'Authors': d.document_info.authors,
                             'DOI': d.document_info.doi,
                             'Journal': d.document_info.journal
                             }

                    data_records.append(entry)
        return data_records


class MagnetismDatabase:
    def __init__(self, file_dir, db_name, number_of_articles=None, start=0):

        self.properties = {'Curie Temperatures': CurieTemperatureData(), 'Néel Temperatures': NeelTemperatureData()}
        self.client = MongoClient()
        self.db_name = db_name
        self.db = self.client[self.db_name]
        self.from_files(file_dir, number_of_articles, start)

    def from_files(self, file_dir, number_of_articles=None, start=0):
        """ Create database records for each file in the given directory """
        if not exists(file_dir):
            raise FileExistsError

        counter = start
        if number_of_articles is None:
            number_of_articles = len(os.listdir(file_dir)) - start

        for filename in os.listdir(file_dir)[start:start+number_of_articles]:
            if filename.endswith(('.html', '.xml')):
                try:
                    new_data = []
                    print('Processing', counter, "/", start+number_of_articles, ":", filename)
                    d = Doc().from_file(file_dir + filename)
                    for label, prprty in self.properties.items():
                        cde_entries = prprty.from_doc(d)
                        print("cde:", cde_entries)
                        for i in cde_entries:
                            new_data.append(i)

                        # Sort the data
                        new_data = sorted(new_data, key=lambda t: t['DOI'])

                    # Remove entries with blank compounds or units
                    to_remove = []
                    for entry in new_data:
                        if not entry['Names'] or entry['Names'] == [[]] or entry['Extracted Units'] is None:
                            to_remove.append(new_data.index(entry))
                    for index in sorted(to_remove, reverse=True):
                        del new_data[index]

                    # save to database
                    if new_data:
                        self.save(new_data)
                except Exception as e:
                    traceback.print_exc(file=sys.stdout)
                    counter += 1
                    continue
            counter += 1

        return

    def save(self, data):
        """ save data to a pyMongo Database"""
        entries = self.db.posts
        entries.insert_many(data)

        return






