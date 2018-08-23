#!/usr/bin/python
# ---------------------------------------------------------------------------
# File: lpex2.py
# Version 12.8.0
# ---------------------------------------------------------------------------
# Licensed Materials - Property of IBM
# 5725-A06 5725-A29 5724-Y48 5724-Y49 5724-Y54 5724-Y55 5655-Y21
# Copyright IBM Corporation 2009, 2017. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with
# IBM Corp.
# ---------------------------------------------------------------------------
"""
Reading and optimizing a problem.  Demonstrates specifying
optimization method by setting parameters.

The user has to choose the method on the command line:

   python lpex2.py <filename> o     cplex default
   python lpex2.py <filename> p     primal simplex
   python lpex2.py <filename> d     dual simplex
   python lpex2.py <filename> b     barrier
   python lpex2.py <filename> h     barrier with crossover
   python lpex2.py <filename> s     sifting
   python lpex2.py <filename> c     concurrent
"""

from __future__ import print_function

import sys

import cplex
from cplex.exceptions import CplexSolverError
import numpy as np
np.set_printoptions(threshold=np.nan)
def lpex2(filename, method):
    c = cplex.Cplex(filename)

    alg = c.parameters.lpmethod.values

    if method == "o":
        c.parameters.lpmethod.set(alg.auto)
    elif method == "p":
        c.parameters.lpmethod.set(alg.primal)
    elif method == "d":
        c.parameters.lpmethod.set(alg.dual)
    elif method == "b":
        c.parameters.lpmethod.set(alg.barrier)
        c.parameters.barrier.crossover.set(
            c.parameters.barrier.crossover.values.none)
    elif method == "h":
        c.parameters.lpmethod.set(alg.barrier)
    elif method == "s":
        c.parameters.lpmethod.set(alg.sifting)
    elif method == "c":
        c.parameters.lpmethod.set(alg.concurrent)
    else:
        raise ValueError(
            'method must be one of "o", "p", "d", "b", "h", "s" or "c"')

    try:
        c.solve()
    except CplexSolverError:
        print("Exception raised during solve")
        return

    # solution.get_status() returns an integer code
    status = c.solution.get_status()
    print(c.solution.status[status])
    if status == c.solution.status.unbounded:
        print("Model is unbounded")
        return
    if status == c.solution.status.infeasible:
        print("Model is infeasible")
        return
    if status == c.solution.status.infeasible_or_unbounded:
        print("Model is infeasible or unbounded")
        return

    s_method = c.solution.get_method()
    s_type = c.solution.get_solution_type()

    print("Solution status = ", status, ":", end=' ')
    # the following line prints the status as a string
    print(c.solution.status[status])
    print("Solution method = ", s_method, ":", end=' ')
    print(c.solution.method[s_method])

    if s_type == c.solution.type.none:
        print("No solution available")
        return
    print("Objective value = ", c.solution.get_objective_value())

    if s_type == c.solution.type.basic:
        basis = c.solution.basis.get_basis()[0]
    else:
        basis = None

    print()

    x = c.solution.get_values(0, c.variables.get_num() - 1)

    infeas = c.solution.get_float_quality(
        c.solution.quality_metric.max_primal_infeasibility)
    print("Maximum bound violation = ", infeas)
    print(np.array(x))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ["o", "p", "d", "b",
                                                 "h", "s", "c"]:
        print("Usage: lpex2.py filename algorithm")
        print("  filename   Name of a file, with .mps, .lp, or .sav")
        print("             extension, and a possible, additional .gz")
        print("             extension")
        print("  algorithm  one of the letters")
        print("             o default")
        print("             p primal simplex")
        print("             d dual simplex")
        print("             b barrier")
        print("             h barrier with crossover")
        print("             s sifting")
        print("             c concurrent")
        sys.exit(-1)
    lpex2(sys.argv[1], sys.argv[2])
