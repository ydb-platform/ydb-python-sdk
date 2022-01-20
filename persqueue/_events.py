#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections


SESSION_CREATED_MARKER = "SESSION_CREATED"

CreateActorEvent = collections.namedtuple(
    'CreateActorEvent',
    ["actor_type", "actor_uid", "configurator", "create_future_id", "death_future_id", "credentials_proto"]
)
DestroyActorEvent = collections.namedtuple('DestroyActorEvent', ["actor_uid"])

ActorStartedEvent = collections.namedtuple('ActorStartedEvent', ["actor_uid", "result"])
ActorStoppedEvent = collections.namedtuple('ActorStoppedEvent', ["actor_uid", "result"])
ActorDeadEvent = collections.namedtuple('ActorDeadEvent', ["actor_uid", "result"])

RenewTicketRequest = collections.namedtuple('RenewTicketRequest', ["actor_uid", "content"])
RenewTicketResponse = collections.namedtuple('RenewTicketResponse', ["actor_uid", "credentials_proto"])

SendRequestEvent = collections.namedtuple(
    'SendRequestEvent', ["actor_uid", "request_type", "request_args", "future_id"])
ResponseReceivedEvent = collections.namedtuple('ResponseReceivedEvent', ["session_id", "response"])
SessionClientReconnectEvent = collections.namedtuple('SessionClientReconnectEvent', ["schedule_after", "endpoint"])


class ReactorStartedEvent(object):
    pass


class StopReactorEvent(object):
    pass


class ConnectionReadyEvent(object):
    def __init__(self, future, key):
        self.future = future
        self.key = key


def session_created_event(session_id):
    return ResponseReceivedEvent(
        session_id,
        response=SESSION_CREATED_MARKER
    )
