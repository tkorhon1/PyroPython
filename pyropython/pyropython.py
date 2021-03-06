# -*- coding: utf-8 -*-

import sklearn.ensemble as skl
from pyropython.initial_design import make_initial_design
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import freeze_support
import numpy as np
import argparse
from pyropython.config import read_config
from pyropython.utils import ensure_dir, read_initial_design
from pyropython.optimizer import get_optimizer
import sys
from datetime import datetime

def optimize_model(case, run_opts):
    """
    Main optimization loop
    """

    """ these can perhaps be changed later to use MPI
       The executor needs to be *PROCESS*PoolExecutor, not *THREAD*Pool
       The Model class and associated functions are not thread safe.
    """
    print("Numebr of parallel jobs: %d" % run_opts.num_jobs)
    ex = ProcessPoolExecutor(run_opts.num_jobs)
    print("Optimizer name: %s" % run_opts.optimizer_name )
    optimizer = get_optimizer(run_opts.optimizer_name)

    if run_opts.initial_design_file is not None:
        print("Initial design from file: {0}".format(run_opts.initial_design_file))
        param_names = [name for name,bounds in case.params]
        initial_design, fvals = read_initial_design(run_opts.initial_design_file,param_names)
        n_points = len(initial_design)
        if fvals is not None:
            n_vals = len(fvals)
        else:
            n_vals = 0 
    else:
        print("Initial design: {0}".format(run_opts.initial_design))
        initial_design = make_initial_design(name=run_opts.initial_design,
                            num_points=run_opts.num_initial,
                            bounds=case.get_bounds())
        fvals = None

    startTime = datetime.now()
    print('\nTime: ', startTime)
    x_best, f_best, Xi, Fi = optimizer(case, run_opts, ex, initial_design, fvals)
    print('\nTime elapsed: ',datetime.now() - startTime)
    X = np.vstack(Xi)
    Y = np.hstack(Fi).T

    print("\nOptimization finished. The best result found was:")
    for n, (name, bounds) in enumerate(case.params):
        print("{name} :".format(name=name), x_best[n])

    # Fit a tree model to get variable importance
    forest = skl.ExtraTreesRegressor()
    forest.fit(X, Y)

    importances = forest.feature_importances_
    names = [name for name, bounds in case.params]
    indices = np.argsort(importances)[::-1]
    # Print the feature ranking
    print("\nVariable importance scores:")
    n_features = len(x_best)
    for f in range(n_features):
        print(("{n}.  {var} :" +
               " ({importance:.3f})").format(
            n=f + 1,
            var=names[indices[f]],
            importance=importances[indices[f]])
        )

    return


def proc_commandline():
    parser = argparse.ArgumentParser()
    parser.add_argument("fname", help="Input file name")
    parser.add_argument("-v", "--verbosity", type=int,
                        help="increase output verbosity")
    parser.add_argument("-n", "--num_jobs", type=int,
                        help="number of concurrent jobs")
    parser.add_argument("-m", "--max_iter", type=int,
                        help="maximum number of iterations")
    parser.add_argument("-i", "--num_initial", type=int,
                        help="number of points in initial design")
    parser.add_argument("-p", "--num_points", type=int,
                        help="number of points per iteration")
    args = parser.parse_args()
    case, run_opts = read_config(args.fname)
    if args.num_jobs:
        run_opts.num_jobs = args.num_jobs
    if args.max_iter:
        run_opts.max_iter = args.max_iter
    if args.num_initial:
        run_opts.num_initial = args.num_initials
    return case, run_opts


def create_dirs(run_opts):
    ensure_dir(run_opts.output_dir)
    ensure_dir("Work/")
    ensure_dir(run_opts.fig_dir)


def main():
    case, run_opts = proc_commandline()
    case.print_info()
    create_dirs(run_opts)
    optimize_model(case, run_opts)
    print("Done")


if __name__ == "__main__":
    freeze_support()
    main()
