import pymc3 as pm


def def_space(space=None, name=None, squeeze=False):
    if space is None:
        space = np.arange(0, 2, dtype=th.config.floatX)
        space = space[:, None]
    elif np.isscalar(space):
        space_x = np.arange(0, space, dtype=th.config.floatX)
        space_x = space_x[None, :]
        return th.shared(space_x, name, borrow=True), None, None

    if squeeze:
        space = np.squeeze(space)
        if type(space) is np.ndarray:
            space_x = space.astype(th.config.floatX)
            if name is None:
                space_th = None
            else:
                space_th = th.shared(space_x, name, borrow=True)
            if len(space_x.shape) == 1 or space_x.shape[1] == 1:
                space_t = np.squeeze(space_x)
            else:
                space_t = np.arange(len(space_x), dtype=th.config.floatX)
        else:
            space_t = space.index
            space_x = space.astype(th.config.floatX)
            if name is None:
                space_th = None
            else:
                space_th = th.shared(space_x.values, name, borrow=True)
        return space_th, space_x, space_t

    if type(space) is np.ndarray:
        if len(space.shape) < 2:
            space = space[:, None]
        space_x = space.astype(th.config.floatX)
        if name is None:
            space_th = None
        else:
            space_th = th.shared(space_x, name, borrow=True)
        if len(space_x.shape) == 1 or space_x.shape[1] == 1:
            space_t = np.squeeze(space_x)
        else:
            space_t = np.arange(len(space_x), dtype=th.config.floatX)
    else:
        space_t = space.index
        space_x = space.astype(th.config.floatX)
        if len(space.shape) < 2:
            space_x = pd.DataFrame(space_x)
        if name is None:
            space_th = None
        else:
            space_th = th.shared(space_x.values, name, borrow=True)
    return space_th, space_x, space_t.astype(np.int32)


class _StochasticProcess:
    """Abstract class used to define a StochasticProcess.

    Attributes:
        model (pm.Model): Reference to the context pm.Model
    """
    def __init__(self, space=1, location: Mean=None, kernel: Kernel=None, mapping: Mapping=None, noise=True, freedom=None,
                 name=None, inputs=None, outputs=None, hidden=None, description=None, file=None, recompile=False, precompile=False,
                 multioutput=False):


        # Space, Hidden, Observed
        if type(space) is int:
            space = np.random.rand(2, space).astype(dtype=th.config.floatX)
        space_raw = space
        space = space_raw[:2]
        __, self.space_values, self.space_index = def_space(space)
        self.inputs, self.inputs_values, self.observed_index = def_space(space, self.name + '_inputs')
        self.outputs, self.outputs_values, __ = def_space(np.zeros(len(space)), self.name + '_outputs', squeeze=True)


        self.random_th = tt.vector(self.name + '_random_th', dtype=th.config.floatX)
        self.random_scalar = tt.scalar(self.name + '_random_scalar', dtype=th.config.floatX)


        self.random_th.tag.test_value = np.random.randn(len(self.space_values)).astype(dtype=th.config.floatX)
        self.random_scalar.tag.test_value = np.float32(10)

        if hidden is None:
            self.hidden = None
        else:
            self.hidden = np.squeeze(hidden)



        print('Space Dimension: ', self.space_values.shape[1])

        # Hyper-parameters values
        self.params_fixed = DictObj()
        self._fixed_keys = []
        self._fixed_array = None
        self._fixed_chain = None
        self.sampling_dims = None
        self.fixed_dims = None


        self.compiles = DictObj()
        self.compiles_trans = DictObj()
        self.compiles_transf = DictObj()
        print('Init Definition')
        self._define_process()
        print('Definition OK')

        self._compile(precompile)
        self._compile_transforms(precompile)
        print('Compilation OK')

        self.observed(inputs, outputs)

        self.logp_prior = None

        if not multioutput:
            self._compile_logprior()
            #__, self.space_values, self.space_index = def_space(space_raw)
            self.fix_params()

        self.set_space(space_raw, self.hidden)


    def logp_fixed(self, params):
        if len(params) > len(self.sampling_dims):
            params = params[self.sampling_dims]
        self._fixed_array[self.sampling_dims] = params
        return self.model.logp_array(self._fixed_array)

    #@jit
    def _logp_fixed(self, sampling_params):
        self._fixed_array[self.sampling_dims] = sampling_params
        return self.model.logp_array(self._fixed_array)

    def _logp_fixed_prior(self, sampling_params):
        self._fixed_array[self.sampling_dims] = sampling_params
        return self.logp_prior(self._fixed_array)

    def _logp_fixed_like(self, sampling_params):
        self._fixed_array[self.sampling_dims] = sampling_params
        return self.model.logp_array(self._fixed_array) - self.logp_prior(self._fixed_array)

    @jit
    def _dlogp_fixed(self, sampling_params):
        self._fixed_array[self.sampling_dims] = sampling_params
        return self.model.dlogp_array(self._fixed_array)[self.sampling_dims]

    @jit
    def logp_fixed_chain(self, params):
        if len(params) > len(self.sampling_dims):
            params = params[self.sampling_dims]
        return self._logp_fixed_chain(params)

    @jit
    def _logp_fixed_chain(self, sampling_params):
        self._fixed_chain[:, self.sampling_dims] = sampling_params
        out = np.empty(len(self._fixed_chain))
        for i in range(len(out)):
            out[i] = self.model.logp_array(self._fixed_chain[i])
        return out.th_mean()

    @jit
    def _dlogp_fixed_chain(self, sampling_params):
        self._fixed_chain[:, self.sampling_dims] = sampling_params
        out = np.empty((len(self._fixed_chain), len(self.sampling_dims)))
        for i in range(len(out)):
            out[i, :] = self.model.dlogp_array(self._fixed_chain[i])[self.sampling_dims]
        return out.th_mean(axis=0)

