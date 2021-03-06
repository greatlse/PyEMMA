
# This file is part of PyEMMA.
#
# Copyright (c) 2015, 2014 Computational Molecular Biology Group, Freie Universitaet Berlin (GER)
#
# PyEMMA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
import unittest
import numpy as np
from pyemma.msm import bayesian_markov_model
from os.path import abspath, join
from os import pardir


class TestBMSM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # load observations
        import pyemma.datasets
        obs_micro = pyemma.datasets.load_2well_discrete().dtraj_T100K_dt10
        # coarse-grain microstates to two metastable states
        cg = np.zeros(100, dtype=int)
        cg[50:] = 1
        obs_macro = cg[obs_micro]

        # hidden states
        cls.nstates = 2
        # samples
        cls.nsamples = 100

        cls.lag = 100
        cls.sampled_msm_lag100 = bayesian_markov_model(obs_macro, cls.lag, reversible=True, nsamples=cls.nsamples)

    def test_reversible(self):
        assert self.sampled_msm_lag100.is_reversible

    def test_lag(self):
        assert self.sampled_msm_lag100.lagtime == self.lag

    def test_nstates(self):
        assert self.sampled_msm_lag100.nstates == self.nstates

    def test_transition_matrix_samples(self):
        Psamples = self.sampled_msm_lag100.sample_f('transition_matrix')
        # shape
        assert np.array_equal(np.shape(Psamples), (self.nsamples, self.nstates, self.nstates))
        # consistency
        import msmtools.analysis as msmana
        for P in Psamples:
            assert msmana.is_transition_matrix(P)
            assert msmana.is_reversible(P)

    def test_transition_matrix_stats(self):
        import msmtools.analysis as msmana
        # mean
        Pmean = self.sampled_msm_lag100.sample_mean('transition_matrix')
        # test shape and consistency
        assert np.array_equal(Pmean.shape, (self.nstates, self.nstates))
        assert msmana.is_transition_matrix(Pmean)
        # std
        Pstd = self.sampled_msm_lag100.sample_std('transition_matrix')
        # test shape
        assert np.array_equal(Pstd.shape, (self.nstates, self.nstates))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('transition_matrix')
        # test shape
        assert np.array_equal(L.shape, (self.nstates, self.nstates))
        assert np.array_equal(R.shape, (self.nstates, self.nstates))
        # test consistency
        assert np.all(L <= Pmean)
        assert np.all(R >= Pmean)

    def test_eigenvalues_samples(self):
        samples = self.sampled_msm_lag100.sample_f('eigenvalues')
        # shape
        self.assertEqual(np.shape(samples), (self.nsamples, self.nstates))
        # consistency
        for ev in samples:
            assert np.isclose(ev[0], 1)
            assert np.all(ev[1:] < 1.0)

    def test_eigenvalues_stats(self):
        # mean
        mean = self.sampled_msm_lag100.sample_mean('eigenvalues')
        # test shape and consistency
        assert np.array_equal(mean.shape, (self.nstates,))
        assert np.isclose(mean[0], 1)
        assert np.all(mean[1:] < 1.0)
        # std
        std = self.sampled_msm_lag100.sample_std('eigenvalues')
        # test shape
        assert np.array_equal(std.shape, (self.nstates,))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('eigenvalues')
        # test shape
        assert np.array_equal(L.shape, (self.nstates,))
        assert np.array_equal(R.shape, (self.nstates,))
        # test consistency
        assert np.all(L <= mean)
        assert np.all(R >= mean)

    def test_eigenvectors_left_samples(self):
        samples = self.sampled_msm_lag100.sample_f('eigenvectors_left')
        # shape
        np.testing.assert_equal(np.shape(samples), (self.nsamples, self.nstates, self.nstates))
        # consistency
        for evec in samples:
            assert np.sign(evec[0,0]) == np.sign(evec[0,1])
            assert np.sign(evec[1,0]) != np.sign(evec[1,1])

    def test_eigenvectors_left_stats(self):
        # mean
        mean = self.sampled_msm_lag100.sample_mean('eigenvectors_left')
        # test shape and consistency
        assert np.array_equal(mean.shape, (self.nstates, self.nstates))
        assert np.sign(mean[0,0]) == np.sign(mean[0,1])
        assert np.sign(mean[1,0]) != np.sign(mean[1,1])
        # std
        std = self.sampled_msm_lag100.sample_std('eigenvectors_left')
        # test shape
        assert np.array_equal(std.shape, (self.nstates, self.nstates))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('eigenvectors_left')
        # test shape
        assert np.array_equal(L.shape, (self.nstates, self.nstates))
        assert np.array_equal(R.shape, (self.nstates, self.nstates))
        # test consistency
        assert np.all(L <= mean)
        assert np.all(R >= mean)

    def test_eigenvectors_right_samples(self):
        samples = self.sampled_msm_lag100.sample_f('eigenvectors_right')
        # shape
        np.testing.assert_equal(np.shape(samples), (self.nsamples, self.nstates, self.nstates))
        # consistency
        for evec in samples:
            assert np.sign(evec[0,0]) == np.sign(evec[1,0])
            assert np.sign(evec[0,1]) != np.sign(evec[1,1])

    def test_eigenvectors_right_stats(self):
        # mean
        mean = self.sampled_msm_lag100.sample_mean('eigenvectors_right')
        # test shape and consistency
        np.testing.assert_equal(mean.shape, (self.nstates, self.nstates))
        assert np.sign(mean[0,0]) == np.sign(mean[1,0])
        assert np.sign(mean[0,1]) != np.sign(mean[1,1])
        # std
        std = self.sampled_msm_lag100.sample_std('eigenvectors_right')
        # test shape
        assert np.array_equal(std.shape, (self.nstates, self.nstates))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('eigenvectors_right')
        # test shape
        assert np.array_equal(L.shape, (self.nstates, self.nstates))
        assert np.array_equal(R.shape, (self.nstates, self.nstates))
        # test consistency
        assert np.all(L <= mean)
        assert np.all(R >= mean)

    def test_stationary_distribution_samples(self):
        samples = self.sampled_msm_lag100.sample_f('stationary_distribution')
        # shape
        assert np.array_equal(np.shape(samples), (self.nsamples, self.nstates))
        # consistency
        for mu in samples:
            assert np.isclose(mu.sum(), 1.0)
            assert np.all(mu > 0.0)

    def test_stationary_distribution_stats(self):
        # mean
        mean = self.sampled_msm_lag100.sample_mean('stationary_distribution')
        # test shape and consistency
        assert np.array_equal(mean.shape, (self.nstates, ))
        assert np.isclose(mean.sum(), 1.0)
        assert np.all(mean > 0.0)
        assert np.max(np.abs(mean[0]-mean[1])) < 0.05
        # std
        std = self.sampled_msm_lag100.sample_std('stationary_distribution')
        # test shape
        assert np.array_equal(std.shape, (self.nstates, ))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('stationary_distribution')
        # test shape
        assert np.array_equal(L.shape, (self.nstates, ))
        assert np.array_equal(R.shape, (self.nstates, ))
        # test consistency
        assert np.all(L <= mean)
        assert np.all(R >= mean)

    def test_timescales_samples(self):
        samples = self.sampled_msm_lag100.sample_f('timescales')
        # shape
        np.testing.assert_equal(np.shape(samples), (self.nsamples, self.nstates-1))
        # consistency
        for l in samples:
            assert np.all(l > 0.0)

    def test_timescales_stats(self):
        # mean
        mean = self.sampled_msm_lag100.sample_mean('timescales')
        # test shape and consistency
        assert np.array_equal(mean.shape, (self.nstates-1, ))
        assert np.all(mean > 0.0)
        # std
        std = self.sampled_msm_lag100.sample_std('timescales')
        # test shape
        assert np.array_equal(std.shape, (self.nstates-1, ))
        # conf
        L, R = self.sampled_msm_lag100.sample_conf('timescales')
        # test shape
        assert np.array_equal(L.shape, (self.nstates-1, ))
        assert np.array_equal(R.shape, (self.nstates-1, ))
        # test consistency
        assert np.all(L <= mean)
        assert np.all(R >= mean)

    # TODO: these tests can be made compact because they are almost the same. can define general functions for testing
    # TODO: samples and stats, only need to implement consistency check individually.

if __name__ == "__main__":
    unittest.main()