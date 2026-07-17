# -*- coding: utf-8 -*-
import warnings

import pytest

from ydb import convert, table, global_settings


@pytest.fixture(autouse=True)
def _restore_globals():
    truncated = convert._default_allow_truncated_result
    split = table._default_allow_split_transaction
    try:
        yield
    finally:
        convert._default_allow_truncated_result = truncated
        table._default_allow_split_transaction = split


def test_allow_truncated_result_enable_warns_and_updates():
    convert._default_allow_truncated_result = False
    with pytest.warns(UserWarning):
        global_settings.global_allow_truncated_result(True)
    assert convert._default_allow_truncated_result is True


def test_allow_truncated_result_disable_does_not_warn():
    convert._default_allow_truncated_result = True
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        global_settings.global_allow_truncated_result(False)
    assert convert._default_allow_truncated_result is False


def test_allow_truncated_result_noop_when_unchanged():
    convert._default_allow_truncated_result = True
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        global_settings.global_allow_truncated_result(True)
    assert convert._default_allow_truncated_result is True


def test_allow_split_transactions_enable_warns_and_updates():
    table._default_allow_split_transaction = False
    with pytest.warns(UserWarning):
        global_settings.global_allow_split_transactions(True)
    assert table._default_allow_split_transaction is True


def test_allow_split_transactions_disable_does_not_warn():
    table._default_allow_split_transaction = True
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        global_settings.global_allow_split_transactions(False)
    assert table._default_allow_split_transaction is False


def test_allow_split_transactions_noop_when_unchanged():
    table._default_allow_split_transaction = False
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        global_settings.global_allow_split_transactions(False)
    assert table._default_allow_split_transaction is False
