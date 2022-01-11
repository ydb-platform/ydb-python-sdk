#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import time

import kikimr.public.sdk.python.persqueue.grpc_pq_streaming_api as pqlib
import kikimr.public.sdk.python.persqueue.auth as auth
from kikimr.public.sdk.python.persqueue.errors import SessionFailureResult
import concurrent.futures
import logging

"""
Sample contains 2 parts. Common producer and retrying producer.
Steps 0-3 are absolutely equal and will be performed once.
Steps 4 and further are slightly different.
"""

# Setup logging. Especially useful for troubleshooting.
logging.basicConfig(level=logging.INFO)
logging.getLogger("kikimr.public.sdk.python.persqueue").setLevel(logging.DEBUG)


# Parse parameters from command line method
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", action="store", default="test/test", help="Topic to write into (full path)")
    parser.add_argument("--endpoint", default="vla.logbroker.yandex.net", help="data plane API endpoint host")
    _args, _ = parser.parse_known_args()
    return _args


# Step 0. Initialize parameters from command line
args = parse_args()

# Step 1. Prepare API object. Must be created and started prior to any further work
# endpoint port is 2135 on all the installations.
api = pqlib.PQStreamingAPI(args.endpoint, 2135)
# start() returns concurrent.Future object. When start is done, result is set to this future.
print "Starting PqLib"
api_start_future = api.start()
# It is necessary that start() is complete before further work with PqLib.
result = api_start_future.result(timeout=10)
print " Api started with result: {}".format(result)

# Step 2. Prepare credentials provider for authorization.
# Provider with OAuth token is used for samples. Token will be extracted from env.
# See docs for more authorization methods (including TVM).
if 'LOGBROKER_TOKEN' not in os.environ:
    raise RuntimeError("this example expects LOGBROKER_TOKEN env variable to be set")
credentials_provider = auth.OAuthTokenCredentialsProvider(os.environ['LOGBROKER_TOKEN'])

# Step 3. Create configuration of producer. Configurator doesn't depend on anything and may be created at any time.
# extra_fields is optional parameter. See docs for more info.
source_id = "ProducerExampleWriter"
extra_fields = {'key1': 'value1', 'key2': 'value2'}
configurator = pqlib.ProducerConfigurator(args.topic, source_id, extra_fields=extra_fields)

# Example 1. Common producer.
# Step 4. Now create producer itself.
producer = api.create_producer(configurator, credentials_provider=credentials_provider)

# Step 5. Start the producer.
print "Starting Producer"
start_future = producer.start()  # Also available with producer.start_future()
# Wait for producer to start.
start_result = start_future.result(timeout=10)

# Will be used to store latest written SeqNo. See Logbroker basics for more info.
max_seq_no = None

# Result of start should be verified. An error could occur.
if not isinstance(start_result, SessionFailureResult):
    if start_result.HasField("init"):
        print "Producer start result was: {}".format(start_result)
        max_seq_no = start_result.init.max_seq_no
    else:
        raise RuntimeError("Unexpected producer start result from server: {}.".format(start_result))
else:
    raise RuntimeError("Error occurred on start of producer: {}.".format(start_result))
print "Producer started"

# Step 6.1 Write data trivial. Just write single message.
message = "sample_message_single"
# Every next message within one source id must be provided with increasing SeqNo
max_seq_no += 1
# write() requires seq_no and message itself and returns Future() object
# response is a Future object
response = producer.write(max_seq_no, message)
# result will be set when server confirms message written. Result will contain Ack (see protos for more details)
write_result = response.result(timeout=10)
if not write_result.HasField("ack"):
    raise RuntimeError("Message write failed with error {}".format(write_result))
print "Single message written with result: {}".format(write_result)


# Step 6.2 Not write several messages with controlled in-flight
# Here we're going to write that amount of messages
sample_messages_count = 20
# And this is the max request in-flight we are going to have at once
max_inflight = 3
sample_data = ["Sample_message_{}".format(i) for i in range(sample_messages_count)]

# Stop condition for this sample is getting specified count of messages written.
# So just track the progress using counter.
messages_written = 0
# And this counter we use to track which message is next to be sent
current_message = 0
# Here we'll store write responses (Futures).
messages_inflight = []
# Will work until everything is written
while messages_written < sample_messages_count:
    # Send writes until we have desired messages inflight. And skip this step if all massages are sent already.
    while len(messages_inflight) < max_inflight and current_message < sample_messages_count:
        max_seq_no += 1
        messages_inflight.append(producer.write(max_seq_no, sample_data[current_message]))
        current_message += 1
    # Now we got desired inflight count and will wait for some write to complete before sending new writes
    concurrent.futures.wait(
        messages_inflight, timeout=10, return_when=concurrent.futures.FIRST_COMPLETED
    )
    # Actually futures.wait method returns a ready list of completed futures.
    # But here we use a protocol property - it is strictly consecutive and latter calls can only be replied after
    # earlier ones. So we can just go throw the responses list in order of creation.
    completed_count = 0
    for f in messages_inflight:
        if not f.done():
            # Once we hit not completed request, we can stop as all latter requests cannot be completed as well
            break
        # Here the future is expected to be complete already
        result = f.result(timeout=0)
        if isinstance(result, SessionFailureResult) or not result.HasField("ack"):
            raise RuntimeError("Exception occurred during message write {}".format(f.execption()))
        else:
            print "Message written with result: {}".format(result)
            completed_count += 1
    messages_written += completed_count
    # Clear complete requests out of inflight list
    messages_inflight = messages_inflight[completed_count:]
    # And move to another iteration

print "Written {} messages. Done".format(sample_messages_count)

# Step 6.3 Now write data with manually specified create time.
# By default PqLib sets create_time=now(), use this functionality if you need something different, specify it explicitly
# NOTICE: create_time is measured in MILLISECONDS
my_create_time = (int(time.time()) - 5) * 1000  # Now - 5 sec, in milliseconds
message = "sample_message_single"
max_seq_no += 1
response = producer.write(max_seq_no, message, create_time_ms=my_create_time)
write_result = response.result(timeout=10)
if not write_result.HasField("ack"):
    raise RuntimeError("Message write failed with error {}".format(write_result))
print "Single message with create time = {} written with result: {}".format(my_create_time, write_result)

# Step 8. We are done. Now can stop the producer if it's not used anymore.
print "Stop the producer"
producer.stop()

# Step 9.  Stop the PqLib object at the end of all work.
api.stop()
print "DONE"
