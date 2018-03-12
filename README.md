# magdb
Tools for creating a MongoDB collection of phase transitions records from scientific documents. This system makes use
of machine learning and semi-supervised natural language processing within the [ChemDataExtractor toolkit](http://chemdataextractor.org)
and the modified system using semi-supervised relationship extraction [CDESnowball](http://github.com/cjcourt/CDESnowball.git).

**INSTALLATION NOTES**
The database creation tool has been designed using python 3.6.

The toolkit requires MongoDB to be set up and working with python using the PyMongo library, available with pip.
```
  pip3 install pymongo
```
See the [MongoDB](https://docs.mongodb.com) documentation for guidance on setting it up.

You will also require:

- A working version of the latest build of [ChemDataExtractor](http://chemdataextractor.org/download) and all its dependencies
- The modified [ChemDataExtractor_snowball package](https://github.com/cjcourt/CDESnowball)


**USAGE:**
Create a new database using the following:

```
from magdb import MagnetismDatabase

corpus = 'path/to/corpus'
db_name = 'db_test'

# create the database, establish a mongodb connection
db = MagnetismDatabase(db_name)

# run on the corpus
db.from_files(corpus)

# read resulting database
entries = db.database.posts

for record in entries.find():
    print(record)

```
The db_name is an arbitrary string name for the MongoDB collection.

The corpus_dir argument must provide a path to a directory containing scientific articles in XML and/or HTML formats.
Details on how to obtain such documents can be found in the [ChemDataExtractor documentation](http://chemdataextractor.org/docs/intro).
 



