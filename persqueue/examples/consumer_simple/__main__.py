#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import logging

from concurrent.futures import TimeoutError

import kikimr.public.sdk.python.persqueue.grpc_pq_streaming_api as pqlib
import kikimr.public.sdk.python.persqueue.auth as auth
from kikimr.public.sdk.python.persqueue.errors import SessionFailureResult


# Setup logging. Especially useful for troubleshooting.

logging.basicConfig(level=logging.INFO)
logging.getLogger("kikimr.public.sdk.python.persqueue").setLevel(logging.DEBUG)


# Parse parameters from command line method
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", action="store", default="test/test", help="Topic to read from (full path)")
    parser.add_argument(
        "--consumer", action="store", default="shared/testreader", help="Consumer name to use(full path)"
    )
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

# Step 3. Create configuration of consumer. Configurator doesn't depend on anything and may be created at any time.
configurator = pqlib.ConsumerConfigurator(args.topic, args.consumer)

# Step 4. Now create consumer itself.
consumer = api.create_consumer(configurator, credentials_provider=credentials_provider)

# Step 5. Start the consumer.
print "Starting consumer"
start_future = consumer.start()  # Also available with consumer.start_future()
# Wait for consumer to start.
start_result = start_future.result(timeout=10)
# Result of start should be verified. An error could occur.
if not isinstance(start_result, SessionFailureResult):
    if start_result.HasField("init"):
        print "Consumer start result was: {}".format(start_result)
    else:
        raise RuntimeError("Bad consumer start result from server: {}.".format(start_result))
else:
    raise RuntimeError("Error occurred on start of consumer: {}.".format(start_result))
print "Consumer started"

# Step 6. Read some data.
# We expect to read 10 messages - that's the count a producer example provides. There can actually be more messages.
# There may also be no new messages in topic if no one writes anything since last run of this sample.
# You can produce more messages launching producer sample.
total_messages_expected = 20

# In this sample we don't process data, just collect it in a list. Put here your processing instead.
all_data = []
# Cookies are used for commits. Commits confirm we read and processed the message.
# You may either commit every single cookie when all messages from batch are processed or collect several cookies
# and commit them in one pack. In any scenario cookie must be kept before you commit it.
# WARNING: Loosing cookies is a definitely incorrect behavior and will bring just pain

# Last cookie we got
last_received_cookie = None
# Last cookie committed and acked by server
last_committed_cookie = None

print "Read data"
# So here we want to get total_messages_expected confirm receiving with commit() and wait for ack on these commit
# Cookies are committed and acked sequentially so there is no need to match exact set of committed and acked cookies
# Just check the last ones
while total_messages_expected > 0 or last_received_cookie != last_committed_cookie:
    # next_event() returns concurrent.Future object. Result will be set to Future when response is actually received
    # from server
    try:
        result = consumer.next_event().result(timeout=10)
    except TimeoutError:
        raise RuntimeError(
            "Failed to get any messages from topic {}. Are you sure there is any data to read?".format(args.topic)
        )
    # Several result types exist (see docs for more info). Here we care about MSG_DATA which means message with data
    # read from LB or MSG_COMMIT which is ack on commit request (commit requests are sent few lines below).

    if result.type == pqlib.ConsumerMessageType.MSG_DATA:
        for batch in result.message.data.message_batch:
            for message in batch.message:
                all_data.append(message)
                total_messages_expected -= 1
                print "Received message from offset {} with seq_no {}".format(message.offset, message.meta.seq_no)
                if total_messages_expected == 0:
                    # This is a signal to consumer that you are not willing to receive any more messages.
                    # NOTICE: you still may get some messages that were already read ahead on in flight when this
                    # method was called. But consumer won't read anything new after that.
                    consumer.reads_done()
        # Now commit the cookie to confirm we got and processed this message
        consumer.commit(result.message.data.cookie)
        last_received_cookie = result.message.data.cookie
    else:
        # No other message types are expected in this sample
        assert result.type == pqlib.ConsumerMessageType.MSG_COMMIT
        last_committed_cookie = result.message.commit.cookie[-1]


print "Reads done. Totally read {} messages".format(len(all_data))

# Step 9. We are done. Now can stop the producer if it's not used anymore.
print "Stop the consumer"
consumer.stop()

# Step 10.  Stop the PqLib object at the end of all work.
api.stop()
print "DONE"
