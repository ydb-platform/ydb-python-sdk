import os
import collections
import hashlib
import json

from kikimr.library.ci.common import yatest_common


def test_hashes_requires_update_of_versions_and_changelog():
    """"
    Если у вас упал этот тест, то:
      1. канонизируйте его: ya make -rtA --canonize-tests
      2. обновите очередную версию sdk в kikimr/public/sdk/python/client/ydb_version.py
      3. напишите про изменение в CHANGELOG.md
    """

    relative_from = yatest_common.source_path("kikimr/public/sdk/python")
    queue = collections.deque([
        yatest_common.source_path("kikimr/public/sdk/python")
    ])

    skip_calculation_for = set([
        yatest_common.source_path("kikimr/public/sdk/python/ut"),
        yatest_common.source_path("kikimr/public/sdk/python/examples"),
        yatest_common.source_path("kikimr/public/sdk/python/persqueue/examples"),
        yatest_common.source_path("kikimr/public/sdk/python/client/ydb_version.py"),
    ])

    hashes = {}
    while len(queue) > 0:
        dr = queue.popleft()

        for child in os.listdir(dr):
            fp = os.path.join(dr, child)

            if fp in skip_calculation_for:
                continue

            if fp.endswith('ya.make'):
                continue

            if os.path.isdir(fp):
                queue.append(fp)
            else:

                with open(fp, 'r') as r:
                    data = r.read()

                hashes.update({
                    os.path.relpath(fp, relative_from): hashlib.md5(data).hexdigest()
                })

    f = yatest_common.output_path("GOLDEN")
    with open(f, 'w') as golden:
        golden.write(json.dumps(hashes, indent=4))
    return yatest_common.canonical_file(f)
