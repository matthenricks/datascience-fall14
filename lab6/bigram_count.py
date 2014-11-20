from pyspark import SparkContext, SparkConf
import sys

textPath = sys.argv[1]
#textPath = "bible+shakes.nopunc"

# Start and link to a running instance of Spark
conf = SparkConf().setAppName("BigramCount").setMaster("local")
sc = SparkContext(conf=conf)

# Import in the text file
tFile = sc.textFile(textPath)

# Function to do a bigram mapping
def bigram_mapper(line):
    retArr = []
    line = line.split(" ")
    if len(line) > 1:
        for i in range(1, len(line)):
            retArr += [(line[i-1] + " " + line[i], 1)]
    return retArr

counts = tFile.flatMap(lambda line: bigram_mapper(line)).reduceByKey(lambda a, b: a + b)

#print counts.sortByKey().take(100)

# Remap the bigram to all of the words and group it
def bigram_word_map(bcount):
    bigram, count = bcount
    bigram = bigram.split(" ")
    if len(bigram) != 2:
        print "Bigram incorrect size: ", bigram
        raise
    left, right = bigram
    
    retArr = []
    retArr = retArr + [(left, bcount)]
    retArr = retArr + [(right, bcount)]
    return retArr

word_bigram_mapping = counts.flatMap(bigram_word_map)

top_count = 5

# Now, take the max from the word-bigram mapping
def bigram_word_reducer(itera):
    top = [None for x in range(0,top_count)]
    for bigram in itera:
        val = int(bigram[1])
        for i in range(0, len(top)):
            if (top[i] == None):
                # This means it is null at the point.
                # Only if it's the last one, do something
                if i == len(top)-1:
                    top[i] = bigram
            elif val < int(top[i][1]):
                if i > 0:
                    top[i-1] = bigram
                    break
            else:
                # The value is greater than or equal to the current value!
                if i > 0:
                    top[i-1] = top[i]
                    # If at the end of the array, place yourself on!
                    if i == len(top) - 1:
                        top[i] = bigram
    res = []
    for i in reversed(range(0, len(top))):
        if (top[i] == None):
            break
        res = res + [top[i]]
    return res


word_top_bigrams = word_bigram_mapping.groupByKey().map(lambda x: (x[0], bigram_word_reducer(x[1])))

word_top_bigrams.saveAsTextFile("output")

sc.stop()
