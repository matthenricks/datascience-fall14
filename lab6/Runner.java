package main;

import java.io.IOException;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapred.FileInputFormat;
import org.apache.hadoop.mapred.FileOutputFormat;
import org.apache.hadoop.mapred.JobClient;
import org.apache.hadoop.mapred.JobConf;
import org.apache.hadoop.mapred.MapReduceBase;
import org.apache.hadoop.mapred.Mapper;
import org.apache.hadoop.mapred.OutputCollector;
import org.apache.hadoop.mapred.Reducer;
import org.apache.hadoop.mapred.Reporter;
import org.apache.hadoop.mapred.TextInputFormat;
import org.apache.hadoop.mapred.TextOutputFormat;


public class Runner {

	private static class bigramCreator {
		
	    public static class Map extends MapReduceBase implements Mapper<LongWritable, Text, Text, IntWritable> {
	        private final static IntWritable one = new IntWritable(1);
	        private Text word = new Text();

	        public void map(LongWritable key, Text value, OutputCollector<Text, IntWritable> output, Reporter reporter) throws IOException {
	            String line = value.toString();
	            StringTokenizer tokenizer = new StringTokenizer(line);

	            String[] gram = new String[2];
				if (tokenizer.countTokens() > 2) {
					gram[0] = tokenizer.nextToken();
					gram[1] = tokenizer.nextToken();
					word.set(gram[0] + " " + gram[1]);
					output.collect(word, one);
				}
				
	            while (tokenizer.hasMoreTokens()) {
	            	gram[0] = gram[1];
	            	gram[1] = tokenizer.nextToken();
					word.set(gram[0] + " " + gram[1]);
					output.collect(word, one);
	            }
	        }
	    }

	    public static class Reduce extends MapReduceBase implements Reducer<Text, IntWritable, Text, IntWritable> {
	        public void reduce(Text key, Iterator<IntWritable> values, OutputCollector<Text, IntWritable> output, Reporter reporter) throws IOException {
	            int sum = 0;
	            while (values.hasNext()) {
	                sum += values.next().get();
	            }
	            output.collect(key, new IntWritable(sum));
	        }
	    }		
	}
	
	private static class bigramProcessor {
	   
		public static class Map extends MapReduceBase implements Mapper<LongWritable, Text, Text, Text> {
		   
		   private Text countedGram = new Text();
		   private Text word = new Text();
		   public void map(LongWritable key, Text value, OutputCollector<Text, Text> output, Reporter reporter) throws IOException {
		
			   String[] parts = value.toString().split("\t");
			   if (parts.length != 2) {
				   System.err.println("Error in size of the split - " + value.toString());
					return;
			   }
			   
			   String[] bigram = parts[0].toString().split(" ");
			   if (bigram.length != 2) {
			   System.err.println("Error in size of the bigram - " + key);
				   return;
			   }
			   
			   // print out the bigrams
			   countedGram.set(parts[0] + " " + parts[1]);
			   word.set(bigram[0]);
			   output.collect(word, countedGram);
			   word.set(bigram[1]);
			   output.collect(word, countedGram);
		   }
		}
		
	    public static class Reduce extends MapReduceBase implements Reducer<Text, Text, Text, Text> {
	    	
	    	static final int arraySize = 5;
	    	
	        public void reduce(Text key, Iterator<Text> values, OutputCollector<Text, Text> output, Reporter reporter) throws IOException {	        	
	        	
	        	String[] topLeft = new String[arraySize];
	        	String[] topRight = new String[arraySize];
	        	Integer[] topVal = new Integer[arraySize];
	        	
	        	while (values.hasNext()) {
	        		// Now, we can split it in 3
	        		Text temp = values.next();
	        		String[] bigramVal = temp.toString().split(" ");
	        		
	        		if (bigramVal.length != 3) {
	        			throw new Error("Split didn't transfer correctly - " + temp.toString());
	        		}
	        		
	        		Integer tempVal = Integer.parseInt(bigramVal[2]);
	        		
	        		for (int i = 0; i < arraySize; i++) {
	            		// [5th, 4th, ..., 1st]
	            		if (topLeft[i] == null) {
	            			// Continue - until not null or final
	            			if (i == arraySize - 1) {
		            			topLeft[i] = bigramVal[0];
		            			topRight[i] = bigramVal[1];
		            			topVal[i] = tempVal;
	            			}
	            		} else if (tempVal.compareTo(topVal[i]) >= 0) {
	            			// The input is greater than the space in the array
	            			if (i > 0) {	            				
	            				// Decrement the current array
	            				topLeft[i-1] = topLeft[i];
	            				topRight[i-1] = topRight[i];	            				
	            				topVal[i-1] = topVal[i];
	            				// If at the end, place the value there
	            				if (i == arraySize - 1) {
	    	            			topLeft[i] = bigramVal[0];
	    	            			topRight[i] = bigramVal[1];
	    	            			topVal[i] = tempVal;
	            				}
	            			}
	            		} else {
	            			// If less than the current space, place in the previous
	            			if (i > 0) {
		            			topLeft[i-1] = bigramVal[0];
		            			topRight[i-1] = bigramVal[1];
		            			topVal[i-1] = tempVal;
	            				break;
	            			}
	            		}
	            	}
	            }
	        	
	        	StringBuffer outputBuff = new StringBuffer();
	        	for (int i = arraySize - 1; i >= 1; i--) {
	        		if (topVal[i] != null)
	        			outputBuff.append("<" + topLeft[i] + " " + topRight[i] + ", " + topVal[i].toString() + "> ");
	        	}
        		if (topVal[0] != null)
	        		outputBuff.append("<" + topLeft[0] + " " + topRight[0] + ", " + topVal[0].toString() + ">");
	        	
	            output.collect(key, new Text(outputBuff.toString()));
	        }
	    }
   }
   
   public static void main(String[] args) throws Exception {
     JobConf conf = new JobConf(bigramCreator.class);
     conf.setJobName("bigram_count");

     conf.setOutputKeyClass(Text.class);
     conf.setOutputValueClass(IntWritable.class);

     conf.setMapperClass(bigramCreator.Map.class);
     conf.setCombinerClass(bigramCreator.Reduce.class);
     conf.setReducerClass(bigramCreator.Reduce.class);

     conf.setInputFormat(TextInputFormat.class);
     conf.setOutputFormat(TextOutputFormat.class);

     FileInputFormat.setInputPaths(conf, new Path(args[0]));
     FileOutputFormat.setOutputPath(conf, new Path(args[1]));

     JobClient.runJob(conf);
     
     // Run the second job

     conf = new JobConf(bigramProcessor.class);
     conf.setJobName("word_bi_max");

     conf.setOutputKeyClass(Text.class);
     conf.setOutputValueClass(Text.class);

     conf.setMapperClass(bigramProcessor.Map.class);
     conf.setReducerClass(bigramProcessor.Reduce.class);
     
     conf.setInputFormat(TextInputFormat.class);
     conf.setOutputFormat(TextOutputFormat.class);

     FileInputFormat.setInputPaths(conf, new Path(args[1]));
     FileOutputFormat.setOutputPath(conf, new Path(args[2]));

     JobClient.runJob(conf);
   }
}