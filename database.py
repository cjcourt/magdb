# -*- coding: utf-8 -*-
"""
 Database.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

MongoDB database generator for properties extracted by chemdataextractor-snowball

"""
from record import NeelTemperature, CurieTemperature
from utils import exists, get_chemical_records, get_document_info
from pymongo import MongoClient
import os
import traceback
import sys


class Doc:
    """ Document wrapper object containing all chemical records from ChemDataExtractor and document information
        from CDE scrapers"""

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

        :param r:
        :return:
        """
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
    def __init__(self, db_name, corpus_dir, record_types=None):
        """
        :param db_name: Name of the MongoDb collection
        :param corpus_dir: Path to corpus of articles in XML/HTML format
        :param record_types: Optional, which records data types to include within database, default all available
        """
        if record_types:
            self.record_types = record_types
        else:
            self.record_types = [NeelTemperature(), CurieTemperature()]

        # Set up mongo client
        self.client = MongoClient()
        self.db = self.client[db_name]

        # Initiate
        self.from_files(corpus_dir)

    def save(self, data):
        """
        Save data to a pyMongo Database
        :param data: list of entry dicts
        :return:
        """
        print("saving")
        entries = self.db.posts
        entries.insert_many(data)
        return

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
                    d = Doc().from_file(file_dir + filename)
                    new_data = d.data(self.record_types)
                    # save to database
                    if new_data:
                        self.save(new_data)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    counter += 1
                    continue
            counter += 1
        return






