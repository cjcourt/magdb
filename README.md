# magdb
Tools for creating a MongoDB collection of ChemDataExtractor-snowball records

**USAGE:**
Create a new database using the following:
```
db = MagnetismDatabase(db_name, corpus_dir)
```
- :param db_name: Name of the MongoDb collection
- :param corpus_dir: Path to directory containing corpus of articles in XML/HTML format
- :param record_types: Optional, which records data types to include within database, default all available

Currently the system can only produce Néel and Curie temperature records.


**REQUIREMENTS:**
This requires mongoDB to be set up and working with python using the PyMongo library, available with pip.
```
  pip3 install pymongo
  
```
See the [MongoDB](https://docs.mongodb.com) documentation for guidance on setting it up.
 



