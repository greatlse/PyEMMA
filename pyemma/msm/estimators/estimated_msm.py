
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
from six.moves import range
__author__ = 'noe'

import copy

import numpy as np

from pyemma.msm.models.msm import MSM
from pyemma.util.annotators import alias, aliased
from pyemma.util.units import TimeUnit

@aliased
class EstimatedMSM(MSM):
    r"""Estimated Markov state model"""

    def __init__(self, dtrajs, dt_traj, lag, connectivity, active_set, connected_sets,
                 C_full, C_active, transition_matrix):
        r"""Estimates a Markov model from discrete trajectories.

        Parameters
        ----------
        dtrajs : list containing ndarrays(dtype=int) or ndarray(n, dtype=int)
            discrete trajectories, stored as integer ndarrays (arbitrary size)
            or a single ndarray for only one trajectory.

        dt_traj : str, optional, default='1 step'
            Description of the physical time corresponding to the trajectory time
            step. May be used by analysis algorithms such as plotting tools to
            pretty-print the axes. By default '1 step', i.e. there is no physical
            time unit. Specify by a number, whitespace and unit. Permitted units
            are (* is an arbitrary string):

            |  'fs',  'femtosecond*'
            |  'ps',  'picosecond*'
            |  'ns',  'nanosecond*'
            |  'us',  'microsecond*'
            |  'ms',  'millisecond*'
            |  's',   'second*'

        lagtime : int
            lagtime for the MSM estimation in multiples of trajectory steps

        connectivity : str, optional, default = 'largest'
            Connectivity mode. Three methods are intended (currently only 'largest' is implemented)

            * 'largest' : The active set is the largest reversibly connected set. All estimation will be done on this
              subset and all quantities (transition matrix, stationary distribution, etc) are only defined on this
              subset and are correspondingly smaller than the full set of states
            * 'all' : The active set is the full set of states. Estimation will be conducted on each reversibly connected
              set separately. That means the transition matrix will decompose into disconnected submatrices,
              the stationary vector is only defined within subsets, etc. Currently not implemented.
            * 'none' : The active set is the full set of states. Estimation will be conducted on the full set of states
              without ensuring connectivity. This only permits nonreversible estimation. Currently not implemented.

        active_set :

        connected_sets :

        C_full :

        C_active :

        transition_matrix :

        """
        # superclass constructor
        MSM.__init__(self, transition_matrix, dt_model=TimeUnit(dt_traj).get_scaled(lag))

        # Making copies because we don't know what will happen to the arguments after this call
        self.lag = lag
        self.connectivity = copy.deepcopy(connectivity)
        self.active_set = copy.deepcopy(active_set)
        self._dtrajs_full = copy.deepcopy(dtrajs)
        self.dt_traj = dt_traj
        self._C_full = copy.deepcopy(C_full)
        self._C_active = copy.deepcopy(C_active)
        self._connected_sets = copy.deepcopy(connected_sets)

        # calculate secondary quantities
        self._nstates_full = np.shape(C_full)[0]
        # full2active mapping
        self._full2active = -1 * np.ones(self._nstates_full, dtype=int)
        self._full2active[self._active_set] = np.array(list(range(len(self._active_set))), dtype=int)

        # is estimated
        self._is_estimated = True

    def _check_is_estimated(self):
        assert self._is_estimated, 'You tried to access model parameters before estimating it - run estimate first!'

    ################################################################################
    # Basic attributes
    ################################################################################

    @property
    def lagtime(self):
        """
        The lag time at which the Markov model was estimated

        """
        return self.lag

    @property
    def nstates_full(self):
        r""" Number of states in discrete trajectories """
        self._check_is_estimated()
        return self._nstates_full

    @property
    def active_set(self):
        """
        The active set of states on which all computations and estimations will be done

        """
        self._check_is_estimated()
        return self._active_set

    @active_set.setter
    def active_set(self, value):
        self._active_set = value

    @property
    def connectivity(self):
        """Returns the connectivity mode of the MSM """
        return self._connectivity

    @connectivity.setter
    def connectivity(self, value):
        self._connectivity = value

    @property
    def largest_connected_set(self):
        """
        The largest reversible connected set of states

        """
        self._check_is_estimated()
        return self._connected_sets[0]

    @property
    def connected_sets(self):
        """
        The reversible connected sets of states, sorted by size (descending)

        """
        self._check_is_estimated()
        return self._connected_sets

    @property
    @alias('dtrajs_full')
    def discrete_trajectories_full(self):
        """
        A list of integer arrays with the original (unmapped) discrete trajectories:

        """
        self._check_is_estimated()
        return self._dtrajs_full

    @property
    @alias('dtrajs_active')
    def discrete_trajectories_active(self):
        """
        A list of integer arrays with the discrete trajectories mapped to the connectivity mode used.
        For example, for connectivity='largest', the indexes will be given within the connected set.
        Frames that are not in the connected set will be -1.

        """
        self._check_is_estimated()
        # compute connected dtrajs
        self._dtrajs_active = []
        for dtraj in self._dtrajs_full:
            self._dtrajs_active.append(self._full2active[dtraj])

        return self._dtrajs_active

    @property
    def count_matrix_active(self):
        """The count matrix on the active set given the connectivity mode used.

        For example, for connectivity='largest', the count matrix is given only on the largest reversibly connected set.
        Attention: This count matrix has been obtained by sliding a window of length tau across the data. It contains
        a factor of tau more counts than are statistically uncorrelated. It's fine to use this matrix for maximum
        likelihood estimated, but it will give far too small errors if you use it for uncertainty calculations. In order
        to do uncertainty calculations, use the effective count matrix, see:
        :attr:`effective_count_matrix`

        See Also
        --------
        effective_count_matrix
            For a count matrix with effective (statistically uncorrelated) counts.

        """
        self._check_is_estimated()
        return self._C_active

    # TODO: change to statistically effective count matrix!
    @property
    def effective_count_matrix(self):
        """Statistically uncorrelated transition counts within the active set of states

        You can use this count matrix for Bayesian estimation or error perturbation.

        References
        ----------
        [1] Noe, F. (2015) Statistical inefficiency of Markov model count matrices
            http://publications.mi.fu-berlin.de/1699/1/autocorrelation_counts.pdf

        """
        self._check_is_estimated()
        import msmtools.estimation as msmest
        Ceff_full = msmest.effective_count_matrix(self._dtrajs_full, self.lag)
        from pyemma.util.linalg import submatrix
        Ceff = submatrix(Ceff_full, self.active_set)
        return Ceff
        # return self._C_active / float(self.lag)

    @property
    def count_matrix_full(self):
        """
        The count matrix on full set of discrete states, irrespective as to whether they are connected or not.
        Attention: This count matrix has been obtained by sliding a window of length tau across the data. It contains
        a factor of tau more counts than are statistically uncorrelated. It's fine to use this matrix for maximum
        likelihood estimated, but it will give far too small errors if you use it for uncertainty calculations. In order
        to do uncertainty calculations, use the effective count matrix, see: :attr:`effective_count_matrix`
        (only implemented on the active set), or divide this count matrix by tau.

        See Also
        --------
        effective_count_matrix
            For a active-set count matrix with effective (statistically uncorrelated) counts.

        """
        self._check_is_estimated()
        return self._C_full

    @property
    def active_state_fraction(self):
        """The fraction of states in the largest connected set.

        """
        self._check_is_estimated()
        return float(self._nstates) / float(self._nstates_full)

    @property
    def active_count_fraction(self):
        """The fraction of counts in the largest connected set.

        """
        self._check_is_estimated()
        from pyemma.util.discrete_trajectories import count_states

        hist = count_states(self._dtrajs_full)
        hist_active = hist[self.active_set]
        return float(np.sum(hist_active)) / float(np.sum(hist))

    ################################################################################
    # For general statistics
    ################################################################################

    def trajectory_weights(self):
        r"""Uses the MSM to assign a probability weight to each trajectory frame.

        This is a powerful function for the calculation of arbitrary observables in the trajectories one has
        started the analysis with. The stationary probability of the MSM will be used to reweigh all states.
        Returns a list of weight arrays, one for each trajectory, and with a number of elements equal to
        trajectory frames. Given :math:`N` trajectories of lengths :math:`T_1` to :math:`T_N`, this function
        returns corresponding weights:

        .. math::

            (w_{1,1}, ..., w_{1,T_1}), (w_{N,1}, ..., w_{N,T_N})

        that are normalized to one:

        .. math::

            \sum_{i=1}^N \sum_{t=1}^{T_i} w_{i,t} = 1

        Suppose you are interested in computing the expectation value of a function :math:`a(x)`, where :math:`x`
        are your input configurations. Use this function to compute the weights of all input configurations and
        obtain the estimated expectation by:

        .. math::

            \langle a \rangle = \sum_{i=1}^N \sum_{t=1}^{T_i} w_{i,t} a(x_{i,t})

        Or if you are interested in computing the time-lagged correlation between functions :math:`a(x)` and
        :math:`b(x)` you could do:

        .. math::

            \langle a(t) b(t+\tau) \rangle_t = \sum_{i=1}^N \sum_{t=1}^{T_i} w_{i,t} a(x_{i,t}) a(x_{i,t+\tau})


        Returns
        -------
        weights : list of ndarray
            The normalized trajectory weights. Given :math:`N` trajectories of lengths :math:`T_1` to :math:`T_N`,
            returns the corresponding weights:

            .. math::

                (w_{1,1}, ..., w_{1,T_1}), (w_{N,1}, ..., w_{N,T_N})

        """
        self._check_is_estimated()
        # compute stationary distribution, expanded to full set
        statdist_full = np.zeros([self._nstates_full])
        statdist_full[self.active_set] = self.stationary_distribution
        # simply read off stationary distribution and accumulate total weight
        W = []
        wtot = 0.0
        for dtraj in self.discrete_trajectories_full:
            w = statdist_full[dtraj]
            W.append(w)
            wtot += np.sum(W)
        # normalize
        for w in W:
            w /= wtot
        # done
        return W

    ################################################################################
    # Generation of trajectories and samples
    ################################################################################

    @property
    def active_state_indexes(self):
        """
        Ensures that the connected states are indexed and returns the indices
        """
        self._check_is_estimated()
        try:  # if we have this attribute, return it
            return self._active_state_indexes
        except:  # didn't exist? then create it.
            import pyemma.util.discrete_trajectories as dt

            self._active_state_indexes = dt.index_states(self.discrete_trajectories_full, subset=self.active_set)
            return self._active_state_indexes

    def generate_traj(self, N, start=None, stop=None, stride=1):
        """Generates a synthetic discrete trajectory of length N and simulation time stride * lag time * N

        This information can be used
        in order to generate a synthetic molecular dynamics trajectory - see
        :func:`pyemma.coordinates.save_traj`

        Note that the time different between two samples is the Markov model lag time tau. When comparing
        quantities computing from this synthetic trajectory and from the input trajectories, the time points of this
        trajectory must be scaled by the lag time in order to have them on the same time scale.

        Parameters
        ----------
        N : int
            Number of time steps in the output trajectory. The total simulation time is stride * lag time * N
        start : int, optional, default = None
            starting state. If not given, will sample from the stationary distribution of P
        stop : int or int-array-like, optional, default = None
            stopping set. If given, the trajectory will be stopped before N steps
            once a state of the stop set is reached
        stride : int, optional, default = 1
            Multiple of lag time used as a time step. By default, the time step is equal to the lag time

        Returns
        -------
        indexes : ndarray( (N, 2) )
            trajectory and time indexes of the simulated trajectory. Each row consist of a tuple (i, t), where i is
            the index of the trajectory and t is the time index within the trajectory.
            Note that the time different between two samples is the Markov model lag time tau

        See also
        --------
        pyemma.coordinates.save_traj
            in order to save this synthetic trajectory as a trajectory file with molecular structures

        """
        # TODO: this is the only function left which does something time-related in a multiple of tau rather than dt.
        # TODO: we could generate dt-strided trajectories by sampling tau times from the current state, but that would
        # TODO: probably lead to a weird-looking trajectory. Maybe we could use a HMM to generate intermediate 'hidden'
        # TODO: frames. Anyway, this is a nontrivial issue.
        self._check_is_estimated()
        # generate synthetic states
        from msmtools.generation import generate_traj as _generate_traj

        syntraj = _generate_traj(self.transition_matrix, N, start=start, stop=stop, dt=stride)
        # result
        from pyemma.util.discrete_trajectories import sample_indexes_by_sequence

        return sample_indexes_by_sequence(self.active_state_indexes, syntraj)

    def sample_by_state(self, nsample, subset=None, replace=True):
        """Generates samples of the connected states.

        For each state in the active set of states, generates nsample samples with trajectory/time indexes.
        This information can be used in order to generate a trajectory of length nsample * nconnected using
        :func:`pyemma.coordinates.save_traj` or nconnected trajectories of length nsample each using
        :func:`pyemma.coordinates.save_traj`

        Parameters
        ----------
        N : int
            Number of time steps in the output trajectory. The total simulation time is stride * lag time * N
        nsample : int
            Number of samples per state. If replace = False, the number of returned samples per state could be smaller
            if less than nsample indexes are available for a state.
        subset : ndarray((n)), optional, default = None
            array of states to be indexed. By default all states in the connected set will be used
        replace : boolean, optional
            Whether the sample is with or without replacement
        start : int, optional, default = None
            starting state. If not given, will sample from the stationary distribution of P

        Returns
        -------
        indexes : list of ndarray( (N, 2) )
            list of trajectory/time index arrays with an array for each state.
            Within each index array, each row consist of a tuple (i, t), where i is
            the index of the trajectory and t is the time index within the trajectory.

        See also
        --------
        pyemma.coordinates.save_traj
            in order to save the sampled frames sequentially in a trajectory file with molecular structures
        pyemma.coordinates.save_trajs
            in order to save the sampled frames in nconnected trajectory files with molecular structures

        """
        self._check_is_estimated()
        # generate connected state indexes
        import pyemma.util.discrete_trajectories as dt

        return dt.sample_indexes_by_state(self.active_state_indexes, nsample, subset=subset, replace=replace)

    # TODO: add sample_metastable() for sampling from metastable (pcca or hmm) states.
    def sample_by_distributions(self, distributions, nsample):
        """Generates samples according to given probability distributions

        Parameters
        ----------
        distributions : list or array of ndarray ( (n) )
            m distributions over states. Each distribution must be of length n and must sum up to 1.0
        nsample : int
            Number of samples per distribution. If replace = False, the number of returned samples per state could be
            smaller if less than nsample indexes are available for a state.

        Returns
        -------
        indexes : length m list of ndarray( (nsample, 2) )
            List of the sampled indices by distribution.
            Each element is an index array with a number of rows equal to nsample, with rows consisting of a
            tuple (i, t), where i is the index of the trajectory and t is the time index within the trajectory.

        """
        self._check_is_estimated()
        # generate connected state indexes
        import pyemma.util.discrete_trajectories as dt

        return dt.sample_indexes_by_distribution(self.active_state_indexes, distributions, nsample)

    ################################################################################
    # HMM-based coarse graining
    ################################################################################

    def hmm(self, nstates):
        """Estimates a hidden Markov state model as described in [1]_

        Returns
        -------
        hmsm : :class:`MaximumLikelihoodHMSM`

        References
        ----------
        .. [1] F. Noe, H. Wu, J.-H. Prinz and N. Plattner:
            Projected and hidden Markov models for calculating kinetics and metastable states of complex molecules
            J. Chem. Phys. 139, 184114 (2013)

        """
        self._check_is_estimated()
        # run estimate
        from pyemma.msm.estimators.maximum_likelihood_hmsm import MaximumLikelihoodHMSM
        estimator = MaximumLikelihoodHMSM(lag=self.lagtime, nstates=nstates, msm_init=self,
                                          reversible=self.is_reversible, connectivity=self.connectivity,
                                          observe_active=True, dt_traj=self.dt_traj)
        estimator.estimate(self.discrete_trajectories_full)
        return estimator.model

    def coarse_grain(self, nstates, method='hmm'):
        r"""Returns a coarse-grained Markov model.

        Currently only the HMM method described in [1]_ is available for coarse-graining MSMs.

        Returns
        -------
        hmsm : :class:`MaximumLikelihoodHMSM`

        References
        ----------
        .. [1] F. Noe, H. Wu, J.-H. Prinz and N. Plattner:
            Projected and hidden Markov models for calculating kinetics and metastable states of complex molecules
            J. Chem. Phys. 139, 184114 (2013)

        """
        self._check_is_estimated()
        return self.hmm(nstates)