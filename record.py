# -*- coding: utf-8 -*-
"""
 DatabaseCreation.record.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Record types to use in the MongoDb database

All records must derive from BaseRecord and consist of a method records that extracts desired information from the
CDE-snowball Compound entity

"""
from .utils import normalise_temperature
from abc import abstractmethod


class BaseRecord:
    """Abstract base class for a database record"""

    @abstractmethod
    def records(self, compound):
        """Return a list of record dicts
        :param compound: ChemDataExtractor Compound object
        """
        return []


class NeelTemperature(BaseRecord):
    """ Néel temperature property data
    """
    def records(self, compound):
        """
        Get all Néel temperature data from the CDE Compound to create database entry,
            Normalise temperatures to Kelvin
        """
        if not compound.neel_temperatures:
            return []

        records = []
        for nt in compound.neel_temperatures:
            try:
                normed_value, normed_units = normalise_temperature(nt)
            except ValueError as e:
                print(e)
                normed_value, normed_units = None, None

            entry = {'Type': 'Néel',
                     'Names': compound.names,
                     'Extracted Value': nt.value,
                     'Extracted Units': nt.units,
                     'Normalised Value': normed_value,
                     'Normalised Units': normed_units,
                     'Confidence': nt.confidence,
                     }

            records.append(entry)
        return records


class CurieTemperature(BaseRecord):
    """ Curie temperature property data"""

    def records(self, compound):
        """
        Get all Curie temperature data from the CDE Compound to create database
         entry, Normalise temperatures to Kelvin
        """
        if not compound.curie_temperatures:
            return []

        records = []
        for ct in compound.curie_temperatures:
            try:
                normed_value, normed_units = normalise_temperature(ct)
            except ValueError as e:
                print(e)
                normed_value, normed_units = None, None

            entry = {'Type': 'Néel',
                     'Names': compound.names,
                     'Extracted Value': ct.value,
                     'Extracted Units': ct.units,
                     'Normalised Value': normed_value,
                     'Normalised Units': normed_units,
                     'Confidence': ct.confidence,
                     }

            records.append(entry)
        return records
