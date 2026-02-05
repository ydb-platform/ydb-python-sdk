import gc
import logging

from options import parse_options
from root_runner import run_from_args


if __name__ == "__main__":
    args = parse_options()
    gc.disable()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)-8s %(message)s")

    run_from_args(args)
