#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


SESSION_CREATED_MARKER = "SESSION_CREATED"

CreateActorEvent = collections.namedtuple(
    'CreateActorEvent',
    ["actor_type", "actor_uid", "configurator", "create_future_id", "death_future_id", "credentials_proto"]
)
DestroyActorEvent = collections.namedtuple('DestroyActorEvent', ["actor_uid"])

ActorStartedEvent = collections.namedtuple('ActorStartedEvent', ["actor_uid"])
RenewTicketRequest = collections.namedtuple('RenewTicketRequest', ["actor_uid"])
RenewTicketResponse = collections.namedtuple('RenewTicketResponse', ["actor_uid", "credentials_proto"])
ActorStoppedEvent = collections.namedtuple('ActorStoppedEvent', ["actor_uid"])
ActorDeadEvent = collections.namedtuple('ActorDeadEvent', ["actor_uid"])

FutureRunningEvent = collections.namedtuple('FutureRunningEvent', ["future_id"])
FutureSetResultEvent = collections.namedtuple('FutureSetResultEvent', ["future_id", "result"])

SendRequestEvent = collections.namedtuple(
    'SendRequestEvent', ["actor_uid", "request_type", "request_args", "future_id"])
ResponseReceivedEvent = collections.namedtuple('ResponseReceivedEvent', ["session_uid", "response"])


class ConnectionReadyEvent(object):
    def __init__(self, future):
        self.future = future


class StopReactorEvent(object):
    pass


def session_created_event(session_uid):
    return ResponseReceivedEvent(
        session_uid,
        response=SESSION_CREATED_MARKER
    )
