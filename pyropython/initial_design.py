import numpy as np


def make_initial_design(name="rand",
                        num_points=1,
                        bounds=None):
    ndim = len(bounds)
    if name == "rand":
        xhat = random(num_points, ndim)
    elif name == "lhs":
        xhat = latin_hypercube(num_points, ndim)

    # scale variables
    for row in xhat:
        for n, point in enumerate(row):
            row[n] = bounds[0]+point*(bounds[1]-bounds[0])
    return xhat


def latin_hypercube(num_points=1, ndim=1):
    from pyDOE import lhs
    return lhs(ndim,
               samples=num_points,
               criterion="maximin")


def random(num_points=1,ndim=1):
    return np.random.rand(num_points, ndim)