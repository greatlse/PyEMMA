
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
import os
import numpy as np
import tempfile

from pyemma.util.log import getLogger
import pyemma.coordinates as coor
import pyemma.util.types as types
from six.moves import range


logger = getLogger('TestCluster')


class TestCluster(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCluster, cls).setUpClass()
        cls.dtraj_dir = tempfile.mkdtemp()

        # generate Gaussian mixture
        means = [np.array([-3,0]),
                 np.array([-1,1]),
                 np.array([0,0]),
                 np.array([1,-1]),
                 np.array([4,2])]
        widths = [np.array([0.1,0.1]),
                  np.array([0.1,0.1]),
                  np.array([0.1,0.1]),
                  np.array([0.1,0.1]),
                  np.array([0.1,0.1])]
        # data
        cls.nsample = 1000
        cls.T = len(means)*cls.nsample
        cls.X = np.zeros((cls.T, 2))
        for i in range(len(means)):
            cls.X[i*cls.nsample:(i+1)*cls.nsample,0] = widths[i][0] * np.random.randn() + means[i][0]
            cls.X[i*cls.nsample:(i+1)*cls.nsample,1] = widths[i][1] * np.random.randn() + means[i][1]
        # try assigning actual centers:
        cls.centers = np.array([[-3,0],
                                [-1,1],
                                [0,0],
                                [1,-1],
                                [4,2]])
        # assignment
        cls.ass = coor.assign_to_centers(data = cls.X, centers=cls.centers, return_dtrajs=False)

    def test_chunksize(self):
        assert types.is_int(self.ass.chunksize)

    def test_clustercenters(self):
        c = self.ass
        assert c.clustercenters.shape[0] == self.centers.shape[0]
        assert c.clustercenters.shape[1] == 2

    def test_data_producer(self):
        c = self.ass
        assert c.data_producer is not None

    def test_describe(self):
        c = self.ass
        desc = c.describe()
        assert types.is_string(desc) or types.is_list_of_string(desc)

    def test_dimension(self):
        c = self.ass
        assert types.is_int(c.dimension())
        assert c.dimension() == 1

    def test_dtrajs(self):
        c = self.ass
        assert len(c.dtrajs) == 1
        assert c.dtrajs[0].dtype == c.output_type()
        assert len(c.dtrajs[0]) == self.T
        # assignment in this case should be perfect
        for i in range(self.T):
            assert c.dtrajs[0][i] == int(i / self.nsample)

    def test_return_dtrajs(self):
        dtrajs = coor.assign_to_centers(data=self.X, centers=self.centers)
        for dtraj in dtrajs:
            assert types.is_int_vector(dtraj)

    def test_get_output(self):
        c = self.ass
        O = c.get_output()
        assert types.is_list(O)
        assert len(O) == 1
        assert types.is_int_matrix(O[0])
        assert O[0].shape[0] == self.T
        assert O[0].shape[1] == 1

    def test_in_memory(self):
        c = self.ass
        assert isinstance(c.in_memory, bool)

    def test_iterator(self):
        c = self.ass
        for itraj, chunk in c:
            assert types.is_int(itraj)
            assert types.is_int_matrix(chunk)
            assert chunk.shape[0] <= c.chunksize
            assert chunk.shape[1] == c.dimension()

    def test_map(self):
        c = self.ass
        Y = c.transform(self.X)
        assert Y.shape[0] == self.T
        assert Y.shape[1] == 1
        # test if consistent with get_output
        assert np.allclose(Y, c.get_output()[0])

    def test_n_frames_total(self):
        c = self.ass
        c.n_frames_total() == self.T

    def test_number_of_trajectories(self):
        c = self.ass
        c.number_of_trajectories() == 1

    def test_output_type(self):
        c = self.ass
        assert c.output_type() == np.int32

    def test_parametrize(self):
        c = self.ass
        # nothing should happen
        c.parametrize()

    def test_save_dtrajs(self):
        c = self.ass
        prefix = "test"
        extension = ".dtraj"
        outdir = self.dtraj_dir
        c.save_dtrajs(trajfiles=None, prefix=prefix, output_dir=outdir, extension=extension)

        names = ["%s_%i%s" % (prefix, i, extension)
                 for i in range(c.data_producer.number_of_trajectories())]
        names = [os.path.join(outdir, n) for n in names]

        # check files with given patterns are there
        for f in names:
            os.stat(f)

    def test_trajectory_length(self):
        c = self.ass
        assert c.trajectory_length(0) == self.T
        with self.assertRaises(IndexError):
            c.trajectory_length(1)

    def test_trajectory_lengths(self):
        c = self.ass
        assert len(c.trajectory_lengths()) == 1
        assert c.trajectory_lengths()[0] == c.trajectory_length(0)

    def test_wrong_centers_argument(self):
        dim = 3
        data = np.empty((100,dim))
        centers = np.empty((5, dim+1))

        with self.assertRaises(ValueError):
            c = coor.assign_to_centers(data, centers)

    def test_wrong_centers_argument2(self):
        dim = 3
        data = np.empty((100,dim))
        centers = np.empty(1)

        with self.assertRaises(ValueError):
            c = coor.assign_to_centers(data, centers)

if __name__ == "__main__":
    unittest.main()