"""Run each DVC stage by hand with python -m mlops_project.pipeline STAGE."""
import argparse


def main():
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
