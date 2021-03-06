#
# atactk: ATAC-seq toolkit
#
# Copyright 2015 The Parker Lab at the University of Michigan
#
# Licensed under Version 3 of the GPL or any later version
#


"""
Code used in command-line applications.
"""

from __future__ import print_function

import argparse
import sys

import sexpdata


def check_bins_for_overlap(bins):
    """
    Make sure bins don't overlap.

    Parameters
    ----------
    bins: list
        A list of tuples containing (start, end, resolution).

    Raises
    ------
    argparse.ArgumentTypeError
        If any of the bins overlap.

    """

    last_start, last_end = 0, 0
    for bin in bins:
        start, end, resolution = bin
        if start <= last_end:
            raise argparse.ArgumentTypeError("Bin %d-%d overlaps %d-%d." % (start, end, last_start, last_end))
        last_start, last_end = start, end


def parse_bins(bins_string):
    """
    Parse the string representing template size groups.

    The bins are specified as a list of groups, each group comprising
    one or more bins, and ending with a resolution value, which
    controls how many individual cuts in the extended region around
    the feature are aggregated. Within the feature itself, we always
    count the cut points for each base. A complete example:

    (36-149 1) (150-224 225-324 2) (325-400 5)

    With a resolution of 1, every base in the extended region
    around motifs overlapping templates of length 36-149 would be
    scored independently; each base's cut count would be added to
    the matrix.

    The second group, for templates of length 150-224 or 225-324,
    with a resolution of 2, would result in every two bases in the
    extended region around motifs being added together. Then the
    aggregate scores of the two bins in the group would be summed,
    and the result would be added to the matrix.

    The last bin group, (325-400 5), with a resolution of 5, would
    also produce aggregate scores in the extended region, each
    being the sum of five bases' cut counts.

    To illustrate, assume these settings and an imaginary motif 5
    bases long, with a 10-base extended region on either side, and
    for the sake of example pretend that each template length bin
    had the same counts of cut points around the motif, shown
    here::

        extended region     motif     extended region
        ------------------- --------- -------------------
        0 1 2 3 3 4 4 4 4 5 9 2 0 2 7 5 4 4 4 4 3 3 2 1 0

        The scores for the first bin group, (36-149 1):

        extended region     motif     extended region
        ------------------- --------- -------------------
        0 1 2 3 3 4 4 4 4 5 9 2 0 2 7 5 4 4 4 4 3 3 2 1 0

        The scores for the first bin group, (150-224 225-324 2):

        e.r.      motif     e.r.
        --------- --------- ---------
        1 5 7 8 9 9 2 0 2 7 9 8 7 5 1

        The scores for the last bin group, (325-400 5):

        e.r. motif     e.r.
        ---- --------- ----
        9 21 9 2 0 2 7 21 9


    Parameters
    ----------
    bins_string: str
       A list of S-expressions representing groups of bin start and end positions and resolutions.

    Returns
    -------
    list
       A list of lists of tuples of (start, end, resolution).
    """

    bin_groups = sexpdata.loads('(' + bins_string + ')')

    groups = []
    for g, bin_group in enumerate(bin_groups):
        group = []
        try:
            resolution = int(bin_group.pop())
            if resolution < 1:
                raise ValueError
        except ValueError:
            raise argparse.ArgumentTypeError("Resolution in bin group %s is not a positive integer." % g)

        for i, bin_string in enumerate(bin_group):
            bin_string = bin_string.value()
            bin = bin_string.split('-')
            try:
                if len(bin) != 2:
                    raise ValueError
                start, end = [int(s) for s in bin]
                if start > end:
                    start, end = end, start
                    print("Bin %s specified backward; corrected to %d-%d" % (bin_string, start, end), file=sys.stderr)

                group.append((start, end, resolution))
            except ValueError:
                raise argparse.ArgumentTypeError("Bin %s in group %s is malformed." % (i, g))
        groups.append(group)

    # flatten groups to just a list of bins, sort, check for overlaps
    bins = sorted([b for bins in groups for b in bins])
    check_bins_for_overlap(bins)
    return groups
