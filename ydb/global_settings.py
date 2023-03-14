from . import convert
from . import table


def global_allow_truncated_result(enabled: bool = True):
    convert._default_allow_truncated_result = enabled


def global_allow_split_transactions(enabled: bool):
    table._allow_split_transaction = enabled
