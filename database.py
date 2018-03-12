# -*- coding: utf-8 -*-
"""
 Database.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

MongoDB database generator for properties extracted by chemdataextractor-snowball

"""
from .record import NeelTemperature, CurieTemperature
from .utils import exists, get_chemical_records, get_document_info
from pymongo import MongoClient
import os
import traceback
import sys


class Doc:
    """ Document wrapper object containing all chemical records
    from ChemDataExtractor and document information from CDE scrapers"""

    def __init__(self):
        self.chemical_records = None
        self.document_info = None

    def from_file(self, file):
        """ Create Document data object from html/xml file path """
        if not exists(file):
            raise FileExistsError
        print("Scraping chemical records")
        self.chemical_records = get_chemical_records(file)
        print("Scraping document info")
        self.document_info = get_document_info(file)
        print(self.chemical_records)
        return self

    def append_document_info(self, r):
        """
        Add document information to records

        :param r: dictionary of data records
        :type r: dict
        :return: the updated records
        """
        assert(isinstance(r, dict))

        r['Title'] = self.document_info.title
        r['Authors'] = self.document_info.authors
        r['DOI'] = self.document_info.doi
        r['Journal'] = self.document_info.journal
        return r

    def data(self, record_types):
        """
        Output data records as a dict
        :param record_types: types of record to return,
        :return: list of entry dicts
        """
        output_data = []
        for compound in self.chemical_records:
            for record_type in record_types:
                recs = record_type.records(compound)
                for r in recs:
                    r = self.append_document_info(r)
                    output_data.append(r)
        return output_data


class MagnetismDatabase:
    def __init__(self, db_name):
        """
        :param db_name: Name of the MongoDb collection
        :type db_name: str
        :param corpus_dir: Path to corpus of articles in XML/HTML format
        :type corpus_dir: str
        """
        self._record_types = [NeelTemperature(), CurieTemperature()]

        # Set up mongo client
        self._client = MongoClient()
        self._db = self._client[db_name]

    @property
    def database(self):
        return self._db

    @property
    def record_types(self):
        return self._record_types

    def save(self, data):
        """
        Save data to a pyMongo Database
        :param data: list of entry dicts
        :return:
        """
        entries = self._db.posts
        entries.insert_many(data)
        return

    def from_file(self, f):
        d = Doc().from_file(f)
        new_data = d.data(self.record_types)
        return new_data

    def from_files(self, file_dir):
        """ Create database records for each file in the given directory """
        if not exists(file_dir):
            raise FileExistsError
        counter = 0
        num_of_articles = len(os.listdir(file_dir))
        for filename in os.listdir(file_dir):
            if filename.endswith(('.html', '.xml')):
                try:
                    print('Processing', counter, "/", num_of_articles, ":", filename)
                    new_data = self.from_file(file_dir + filename)
                    # save to database
                    if new_data:
                        self.save(new_data)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    counter += 1
                    continue
            counter += 1
        return
