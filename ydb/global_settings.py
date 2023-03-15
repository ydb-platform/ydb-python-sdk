import warnings

from . import convert
from . import table


def global_allow_truncated_result(enabled: bool = True):
    if enabled:
        warnings.warn("Global allow truncated response is deprecated behaviour.")
    else:
        warnings.warn(
            "Global deny truncated response is default behaviour. You don't need call the function."
        )

    convert._default_allow_truncated_result = enabled


def global_allow_split_transactions(enabled: bool):
    if enabled:
        warnings.warn("Global allow truncated response is deprecated behaviour.")
    else:
        warnings.warn(
            "Global deby truncated response is default behaviour. You don't need call the function."
        )

    table._allow_split_transaction = enabled
