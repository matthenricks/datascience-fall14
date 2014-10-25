# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import csv
import collections
import itertools
import os

# <codecell>

def evaluateDuplicates(found_dupes, true_dupes):
    true_positives = found_dupes.intersection(true_dupes)
    false_positives = found_dupes.difference(true_dupes)
    uncovered_dupes = true_dupes.difference(found_dupes)
    print 'found duplicate'
    print len(found_dupes)
    print 'precision'
    print 1 - len(false_positives) / float(len(found_dupes))
    print 'recall'
    print len(true_positives) / float(len(true_dupes))

# <codecell>

trueCluster = 'product_mapping.csv'
true_dupes = set([])
#test_box = {}

with open(trueCluster) as f:
    reader = csv.DictReader(f, delimiter=',', quotechar='"')
    for i, row in enumerate(reader):
        # Checking if the relationship is a 1-1... It's not, it's a many-many :D
#        if test_box.has_key(row['idAmazon']):
#            test_box[row['idAmazon']] += 1
#        else:
#            test_box[row['idAmazon']] = 1
#            
#        if test_box.has_key(row['idGoogleBase']):
#            test_box[row['idGoogleBase']] += 1
#        else:
#            test_box[row['idGoogleBase']] = 1
        
        true_dupes.add(frozenset([row['idAmazon'], row['idGoogleBase']]))
        
#for (iid, count) in test_box.iteritems():
#    if count > 1:
#        print iid, count

# <codecell>

# Read through the values and take the columns necessary. Have two sets: cluster, G; and cluster, A; Merge the two after
# Unknown if canon will exist or not depending on the amount within the cluster. I'll be it won't if 
def process_clusters(filepath):
    clustersAma = {}
    clustersGoog = {}
    with open(filepath) as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        for i, row in enumerate(reader):
            # print row
            if row['source'] == 'amazon':
                if clustersAma.has_key(row['Cluster ID']):
                    clustersAma[row['Cluster ID']].add(row['id'])
                else:
                    clustersAma[row['Cluster ID']] = set([row['id']])
            else:
                if clustersGoog.has_key(row['Cluster ID']):
                    clustersGoog[row['Cluster ID']].add(row['id'])
                else:
                    clustersGoog[row['Cluster ID']] = set([row['id']])

    # Now, run through the clusters and create the pairs
    approx_set = set([])
    for (clusterID, amazonSet) in clustersAma.iteritems():
        if clustersGoog.has_key(clusterID):            
            googleSet = clustersGoog[clusterID]
            for sset in itertools.product(amazonSet, googleSet):
                approx_set.add(frozenset(sset))                
    
    return approx_set
            
test_dupes = process_clusters('products_out.csv')

# <codecell>

evaluateDuplicates(test_dupes, true_dupes)

# <codecell>


