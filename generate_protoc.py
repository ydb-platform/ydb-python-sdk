import os
import pathlib
import shutil

from typing import List
from argparse import ArgumentParser

from grpc_tools import command


def files_filter(dir, items: List[str]) -> List[str]:
    ignored_names = ['.git']

    ignore = []
    for item in items:
        fullpath = os.path.join(dir, item)
        if os.path.isdir(fullpath) and item not in ignored_names:
            continue
        if item.endswith(".proto"):
            continue
        ignore.append(item)

    return ignore


def create_init_files(rootdirpath: str):
    for root, _dirs, _files in os.walk(rootdirpath):
        init_path = pathlib.Path(os.path.join(root, '__init__.py'))
        if not init_path.exists():
            init_path.touch()


def remove_protos(rootdirpath: str):
    for root, _dirs, files in os.walk(rootdirpath):
        for file in files:
            if file.endswith(".proto"):
                os.remove(os.path.join(root, file))


def fix_file_contents(rootdir, protobuf_version: str):
    flake_ignore_line = "# flake8: " + "noqa"  # prevent ignore the file
    package_path = "ydb._grpc." + protobuf_version + ".protos"

    for dirpath, _, fnames in os.walk(rootdir):
        for fname in fnames:
            if not fname.endswith(".py"):
                continue

            with open(os.path.join(dirpath, fname), 'r+t') as f:
                content = f.read()

                # Fix imports
                content = content.replace("from protos", "from " + package_path)

                # Add ignore style check
                content = content.replace("# -*- coding: utf-8 -*-", "# -*- coding: utf-8 -*-\n" + flake_ignore_line)
                f.seek(0)
                f.write(content)


def generate_protobuf(src_proto_dir: str, dst_dir, protobuf_version: str):
    shutil.rmtree(dst_dir, ignore_errors=True)

    shutil.copytree(src_proto_dir, dst_dir, ignore=files_filter)

    command.build_package_protos(dst_dir)
    remove_protos(dst_dir)
    create_init_files(dst_dir)
    fix_file_contents(dst_dir, protobuf_version)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--target-version", default="v4", help="Protobuf version")

    args = parser.parse_args()

    target_dir = "ydb/_grpc/" + args.target_version
    generate_protobuf("ydb-api-protos", target_dir, args.target_version)
