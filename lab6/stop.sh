#!/bin/bash
mapred historyserver stop 
yarn nodemanager stop
yarn resourcemanager stop
hdfs datanode stop
hdfs namenode stop
