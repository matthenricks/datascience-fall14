# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import csv
import re
import collections
import logging
import optparse
from numpy import nan

import dedupe
from unidecode import unidecode

# <headingcell level=2>

# MODEL Section

# <codecell>

# Now, include the cleaning
from gensim import corpora
#from gensim.models.ldamodel import LdaModel
from gensim.models.tfidfmodel import TfidfModel
from nltk.stem.porter import *
from nltk.corpus import stopwords
from nltk.tokenize import WordPunctTokenizer

# <codecell>

# Set up the infrastructure to clean the text
stopset = set(stopwords.words('english'))
stemmer = PorterStemmer()
def cleanText(column):
    tokens = WordPunctTokenizer().tokenize(column)
    clean = [token.lower() for token in tokens if token.lower() not in stopset and len(token) > 2]
    final = [stemmer.stem(word) for word in clean]
    myString = ""
    for x in cleanText(column):
        myString += x + ' '
    return ([myString.split()])

# <codecell>

from gensim.matutils import cossim

# Dictionary Loading
dictionary_path = 'dictionary.mm'
corpus_path = 'corpus.mm'
dictionary = corpora.Dictionary.load('dictionary.mm')
#model_path = 'lda.mm'
model_path = 'tfidf_model.mm'

model = None

if not os.path.isfile(model_path):
    corpus = corpora.MmCorpus('corpus.mm')
    #model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=100, passes=5)
    model = TfidfModel(corpus, id2word=dictionary, normalize=True)
    model.save(model_path)
else:
    #model = LdaModel.load(model_path)
    model = TfidfModel.load(model_path)

#model.print_topics(20)
model.num_docs

def compare_descriptions(desc1, desc2):
    dv_1 = dictionary.doc2bow(desc1.lower().split())
    dv_2 = dictionary.doc2bow(desc2.lower().split())
    
    dv_1 = model[dv_1]
    dv_2 = model[dv_2]
    return cossim(dv_1, dv_2)

# <headingcell level=3>

# END MODEL

# <codecell>

# ## Logging - ADD THIS IN

# Dedupe uses Python logging to show or suppress verbose output. Added for convenience.
# To enable verbose logging, run `python examples/csv_example/csv_example.py -v`
optp = optparse.OptionParser()
optp.add_option('-v', '--verbose', dest='verbose', action='count',
                help='Increase verbosity (specify multiple times for more)'
                )
(opts, args) = optp.parse_args()
log_level = logging.WARNING 
if opts.verbose == 1:
    log_level = logging.INFO
elif opts.verbose >= 2:
    log_level = logging.DEBUG
logging.getLogger().setLevel(log_level)

# <codecell>

# Switch to our working directory and set up our input and out put paths,
# as well as our settings and training file locations
input_file = 'products.csv'
output_file = 'products_out.csv'
settings_file = 'products_learned_settings'
training_file = 'products_training.json'

# <codecell>

def preProcess(column):
    """
    Do a little bit of data cleaning with the help of Unidecode and Regex.
    Things like casing, extra spaces, quotes and new lines can be ignored.
    """
    column = unidecode(column)
    column = re.sub('  +', ' ', column)
    column = re.sub('\n', ' ', column)
    column = column.strip().strip('"').strip("'").lower().strip()
    return column

# <codecell>

def readData(filename):
    """
    Read in our data from a CSV file and create a dictionary of records, 
    where the key is a unique record ID and each value is dict
    """
    data_d = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = [(k, preProcess(v)) for (k, v) in row.items()]
            row_id = row['id']
            data_d[row_id] = dict(clean_row)

    return data_d

# <codecell>

print 'importing data ...'
data_d = readData(input_file)

# <codecell>

# More advanced LDA comparator
def descComparator(field_1, field_2):
    return compare_descriptions(field_1, field_2)

# <codecell>

# Price comparator
gdp_usd = 1.61
def convert_to_US(field):
    if "gbp" in field:
        nums = re.findall(r'\b\d+\.*\d*\b', field)
        return float(nums[0].strip()) * gdp_usd
    else:
        return float(field.strip())
    
import math

def priceComparator(field_1, field_2) :
	# Recognize the currency
    if field_1 and field_2 :
        field_1 = convert_to_US(field_1)
        field_2 = convert_to_US(field_2)
	tolerance = 0.05 * field_1 + field_2
	if (math.fabs(field_1 - field_2) <= tolerance):
		return 1
	else:
		return 0
    else :
        return nan

# <codecell>

# ## Training

if os.path.exists(settings_file):
    print 'reading from', settings_file
    with open(settings_file, 'rb') as f:
        deduper = dedupe.StaticDedupe(f)

else:
    # Here you will need to define the fields dedupe will pay attention to. You also need to define the comparator
    # to be used and specify any customComparators. Please read the dedupe manual for details
    fields = [
        {'field' : 'title', 'type': 'String'},
        {'field' : 'price', 'type': 'Custom', 'has missing':True, 'comparator' : priceComparator},
        {'field' : 'manufacturer', 'type': 'String', 'has missing':True},
        {'field' : 'description', 'type': 'Custom', 'has missing':True, 'comparator' : descComparator}
        ]
    
    # Create a new deduper object and pass our data model to it.
    deduper = dedupe.Dedupe(fields)

    # To train dedupe, we feed it a random sample of records.
    deduper.sample(data_d, 150000)


    # If we have training data saved from a previous run of dedupe,
    # look for it an load it in.
    # __Note:__ if you want to train from scratch, delete the training_file
    if os.path.exists(training_file):
        print 'reading labeled examples from ', training_file
        with open(training_file, 'rb') as f:
            deduper.readTraining(f)

    # ## Active learning
    # Dedupe will find the next pair of records
    # it is least certain about and ask you to label them as duplicates
    # or not.
    # use 'y', 'n' and 'u' keys to flag duplicates
    # press 'f' when you are finished
    print 'starting active labeling...'

    dedupe.consoleLabel(deduper)

    deduper.train()

    # When finished, save our training away to disk
    with open(training_file, 'w') as tf :
        deduper.writeTraining(tf)

    # Save our weights and predicates to disk.  If the settings file
    # exists, we will skip all the training and learning next time we run
    # this file.
    with open(settings_file, 'w') as sf :
        deduper.writeSettings(sf)

# <codecell>

# ## Blocking

print 'blocking...'

# <codecell>

# ## Clustering

# Find the threshold that will maximize a weighted average of our precision and recall. 
# When we set the recall weight to 2, we are saying we care twice as much
# about recall as we do precision.
#
# If we had more data, we would not pass in all the blocked data into
# this function but a representative sample.

threshold = deduper.threshold(data_d, recall_weight=2)

# `match` will return sets of record IDs that dedupe
# believes are all referring to the same entity.

print 'clustering...'
clustered_dupes = deduper.match(data_d, threshold)

print '# duplicate sets', len(clustered_dupes)

# ## Writing Results

# Write our original data back out to a CSV with a new column called 
# 'Cluster ID' which indicates which records refer to each other.

cluster_membership = {}
cluster_id = 0
for (cluster_id, cluster) in enumerate(clustered_dupes):
    id_set, conf_score = cluster
    cluster_d = [data_d[c] for c in id_set]
    canonical_rep = dedupe.canonicalize(cluster_d)
    for record_id in id_set:
        cluster_membership[record_id] = {
            "cluster id" : cluster_id,
            "canonical representation" : canonical_rep,
            "confidence": conf_score
        }

singleton_id = cluster_id + 1

with open(output_file, 'w') as f_output:
    writer = csv.writer(f_output)

    with open(input_file) as f_input :
        reader = csv.reader(f_input)

        heading_row = reader.next()
        heading_row.insert(0, 'Cluster ID')
        canonical_keys = canonical_rep.keys()
        for key in canonical_keys:
            heading_row.append('canonical_' + key)
        heading_row.append('confidence_score')
        
        writer.writerow(heading_row)

        for row in reader:
            row_id = row[1]
            if row_id in cluster_membership:
                cluster_id = cluster_membership[row_id]["cluster id"]
                canonical_rep = cluster_membership[row_id]["canonical representation"]
                row.insert(0, cluster_id)
                for key in canonical_keys:
                    row.append(canonical_rep[key])
                row.append(cluster_membership[row_id]['confidence'])
            else:
                row.insert(0, singleton_id)
                singleton_id += 1
                for key in canonical_keys:
                    row.append(None)
                row.append(None)
            writer.writerow(row)

