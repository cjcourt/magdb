# magdb
Tools for creating a MongoDB collection of materials property records from scientific documents. This system makes use
of machine learning and semi-supervised natural language processing within the [ChemDataExtractor toolkit](http://chemdataextractor.org).

**INSTALLATION NOTES***
The database creation tool has been designed using python 3.6.

The toolkit requires MongoDB to be set up and working with python using the PyMongo library, available with pip.
```
  pip3 install pymongo

```
See the [MongoDB](https://docs.mongodb.com) documentation for guidance on setting it up.

You will also require:
- A working version of the latest build of [ChemDataExtractor](http://chemdataextractor.org/download) and all its dependencies
- The modified [ChemDataExtractor_snowball package](https://github.com/cjcourt/chemdataextractor-snowball)


**USAGE:**
Create a new database using the following:

```
db = MagnetismDatabase(db_name, corpus_dir)

```
The db_name is an arbitrary string name for the MongoDB collection.

The corpus_dir argument must provide a path to a directory containing scientific articles in XML and/or HTML formats.
Details on how to obtain such documents can be found in the [ChemDataExtractor documentation](http://chemdataextractor.org/docs/intro).
 



