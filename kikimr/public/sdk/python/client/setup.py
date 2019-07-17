# -*- coding: utf-8 -*-
import os
import shutil
import setuptools


def get_arcadia_root():
    arcadia_root_candidate = os.path.dirname(os.path.abspath(__file__))
    retries_count = 10
    for _ in range(retries_count):
        if os.path.exists(os.path.join(arcadia_root_candidate, '.arcadia.root')):
            return arcadia_root_candidate
        arcadia_root_candidate = os.path.dirname(arcadia_root_candidate)
    raise RuntimeError("Unable to find .arcadia.root!")


class CopyModules(setuptools.Command):
    description = 'copy proto files into the root directory'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        arcadia_root = get_arcadia_root()

        for relpath in [
            'yql/public/types',
            'yql/public/issue/protos',
            'kikimr/public/api/grpc',
            'kikimr/public/api/protos',
            'kikimr/public/sdk/python/client',
            'kikimr/public/sdk/python/tvm',
            'kikimr/public/sdk/python/iam',
        ]:
            parts = relpath.split('/')

            for p_size in range(1, len(parts) + 1):
                f_path = os.path.join(*tuple(parts[:p_size]))
                if not os.path.exists(f_path):
                    os.mkdir(f_path)

                if not os.path.exists(os.path.join(f_path, '__init__.py')):
                    open(os.path.join(f_path, '__init__.py'), 'a').close()

            source_folder = os.path.join(arcadia_root, relpath)
            for file_name in os.listdir(source_folder):
                if file_name.startswith('setup.py'):
                    continue

                if file_name.endswith('.proto') or file_name.endswith('.py'):
                    shutil.copyfile(
                        os.path.join(source_folder, file_name),
                        os.path.join(relpath, file_name)
                    )


class BuildPackageProtos(setuptools.Command):
    description = 'build svngrpc protobuf modules'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from grpc_tools import command
        command.build_package_protos(self.distribution.package_dir[''])


setuptools.setup(
    name='ydb',
    version='0.0.25',
    description='YDB Python library',
    author='Yandex LLC',
    author_email='ydb@yandex-team.ru',
    url='http://github.com/yandex-cloud/ydb-python-sdk',
    license='Apache 2.0',
    package_dir={'': '.'},
    packages=setuptools.find_packages('.'),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=(
        'protobuf>=3.3.0',
        'grpcio>=1.5.0',
        'enum-compat>=0.0.1'
    ),
    cmdclass={
        'preprocess': CopyModules,
        'build_package_protos': BuildPackageProtos,
    }
)
