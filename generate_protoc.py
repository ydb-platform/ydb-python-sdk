import os
import pathlib
import shutil
from typing import List

from grpc_tools import command


def files_filter(dir, items: List[str]) -> List[str]:
    ignored_dirs = ['protos', '.git']

    ignore = []
    for item in items:
        fullpath = os.path.join(dir, item)
        if os.path.isdir(fullpath) and item not in ignored_dirs:
            continue
        if item.endswith(".proto"):
            continue
        ignore.append(item)

    print("items: ", items)
    print("ignore: ", ignore)
    return ignore


def create_init_files(dir):
    for root, _dirs, _files in os.walk(dir):
        init_path = pathlib.Path(os.path.join(root, '__init__.py'))
        if not init_path.exists():
            init_path.touch()


def replace_protos_dir():
    def replace_dir(src, dst):
        shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=files_filter)
        create_init_files(dst)

    replace_dir("ydb-api-protos", "ydb/public/api/grpc")
    replace_dir("ydb-api-protos/protos", "ydb/public/api/protos")


def remove_protos():
    for root, _dirs, files in os.walk("ydb/public/api"):
        for file in files:
            if file.endswith(".proto"):
                os.remove(os.path.join(root, file))


if __name__ == '__main__':
    replace_protos_dir()
    command.build_package_protos('./ydb/public/api/')
    remove_protos()
