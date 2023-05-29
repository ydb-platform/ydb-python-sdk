import gc

from options import parse_options
from runner import run_from_args


if __name__ == "__main__":
    args = parse_options()
    gc.disable()
    run_from_args(args)
