import gc
import logging

from options import parse_options
from runner import run_from_args

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    args = parse_options()
    gc.disable()
    run_from_args(args)
