#!/usr/bin/env python

# Copyright 2013-2014 DataStax, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

log = logging.getLogger()
#log.setLevel('DEBUG')
log.setLevel('WARN')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

KEYSPACE = "partone"

def main():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)

    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)

    log.info("dropping table...")
    session.execute("""
        DROP TABLE IF EXISTS adtable
        """)

    log.info("creating table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS adtable (
            ownerid int,
    	    adid int,
            numclicks int,
            numimpressions int,
            ctr float,
            PRIMARY KEY (OwnerId, AdId)
        )
        """)

    inputCommand = session.prepare("""
        INSERT INTO adTable (ownerid, adid, numclicks, numimpressions, ctr)
        VALUES (?, ?, ?, ?, ?)
        """)

    inputArgs = [(1,1,1,10),(1,2,0,5),(1,3,1,20),(1,4,0,15),(2,1,0,10),(2,2,0,55),(2,3,0,13),(2,4,0,21),(3,1,1,32),(3,2,0,23),(3,3,2,44),(3,4,1,36)]

    for (oId, aId, nC, nI) in inputArgs:
        log.info("inserting row %d, %d, %d, %d" % (oId, aId, nC, nI))
        session.execute(inputCommand, (oId, aId, nC, nI, float(nC)/float(nI)))

    # Now, lets begin the fun stuff!

    # 	- Find the ctr (numClicks/numImpressions) for each OwnerId, AdId pair.
    mission1 = session.execute_async("SELECT ownerid, adid, ctr FROM adtable")
    try:
        rows = mission1.result()
    except Exception:
        log.exeception()
    
    print "ownerid\tadid\tctr"
    for row in rows:
        print "\t".join([str(row.ownerid), str(row.adid), str(row.ctr)])

    # 	- Compute the ctr for each OwnerId.
    mission2 = session.execute_async("SELECT ownerid, ctr FROM adtable")
    ownerSum = {}
    ownerCount = {}
    try:
        rows = mission2.result()
    except Exception:
        log.exeception()

    for row in rows:
        if ownerSum.has_key(row.ownerid):
            ownerSum[row.ownerid] += row.ctr
            ownerCount[row.ownerid] += 1
        else:
            ownerSum[row.ownerid] = row.ctr
            ownerCount[row.ownerid] = 1

    print "ownerid\tctr"
    for keyval in ownerSum.keys():
        print "\t".join([str(keyval), str(ownerSum[keyval]/ownerCount[row.ownerid])])

    # 	- Compute the ctr for OwnerId = 1, AdId = 3.
    mission3 = session.execute_async("SELECT ownerid, adid, ctr FROM adtable WHERE ownerid = 1 AND adid = 3")
    try:
        rows = mission3.result()
    except Exception:
        log.exeception()
    
    print "ownerid\tadid\tctr"
    for row in rows:
        print "\t".join([str(row.ownerid), str(row.adid), str(row.ctr)])    

    # 	- Compute the ctr for OwnerId = 2.
    mission4 = session.execute_async("SELECT ownerid, ctr FROM adtable WHERE ownerid = 2")

    try:
        rows = mission4.result()
    except Exception:
        log.exeception()

    count = 0
    mySum = 0
    for row in rows:
        mySum += row.ctr
        count += 1

    print "ownerid\tctr"
    print "\t".join(["2", str(mySum/count)])

    # Drop the keyspace
    session.execute("DROP KEYSPACE " + KEYSPACE)

if __name__ == "__main__":
    main()
