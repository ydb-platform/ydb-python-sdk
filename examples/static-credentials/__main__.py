# -*- coding: utf-8 -*-
import argparse

from example import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\033[92mStatic Credentials example.\x1b[0m\n""",
    )
    parser.add_argument("-e", "--endpoint", help="Endpoint url to use", default="grpc://localhost:2136")
    parser.add_argument("-d", "--database", help="Name of the database to use", default="/local")
    parser.add_argument("-u", "--user", help="User to auth with", default="root")
    parser.add_argument("-p", "--password", help="Password from user to auth with", default="1234")

    args = parser.parse_args()

    run(
        endpoint=args.endpoint,
        database=args.database,
        user=args.user,
        password=args.password,
    )
