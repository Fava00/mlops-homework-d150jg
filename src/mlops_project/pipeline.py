"""Run each DVC stage by hand with python -m mlops_project.pipeline STAGE."""
import argparse
import sys


def main():
    # MLflow prints Unicode run links; Windows redirected consoles may use cp1250.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'train', 'evaluate'])
    args = parser.parse_args()
    if args.stage == 'prepare':
        from .preparation import prepare
        prepare()
    elif args.stage == 'train':
        from .training import train
        train()
    else:
        from .evaluation import evaluate
        evaluate()


if __name__ == '__main__':
    main()
