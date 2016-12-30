import pickle
import numpy as np
import pymc3 as pm
import scipy as sp
import theano as th
from g3py.functions import Mean, Kernel, Mapping, KernelSum, WN, tt_to_num, def_space, trans_hypers
from g3py.libs import tt_to_cov, makefn, text_plot, clone
from g3py.models import Model, TGPDist, ConstantStep, RobustSlice
from g3py import config
from ipywidgets import interact
from matplotlib import pyplot as plt
from theano import tensor as tt


class StochasticProcess:
    """Abstract class used to define a StochasticProcess.

    Attributes:
        model (pm.Model): Reference to the context pm.Model
    """
    def __init__(self, space=1, location: Mean=None, kernel: Kernel=None, mapping: Mapping=None, noise=True, freedom=None,
                 name=None, inputs=None, outputs=None, hidden=None, description=None):
        # Name, Description, Factor Graph, Space, Hidden
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
        if description is None:
            self.description = {'title': 'title',
                                'x': 'x',
                                'y': 'y',
                                'text': 'text'}
        else:
            self.description = description
        self.model = Model.get_context()

        # Space, Hidden, Observed
        __, self.space_values, self.space_index = def_space(space)
        self.inputs, self.inputs_values, self.observed_index = def_space(inputs, self.name + '_inputs')
        self.outputs, self.outputs_values, __ = def_space(outputs, self.name + '_outputs', squeeze=True)

        self.space_th = tt.matrix(self.name + '_space_th', dtype=th.config.floatX)
        self.inputs_th = tt.matrix(self.name + '_inputs_th', dtype=th.config.floatX)
        self.outputs_th = tt.vector(self.name + '_outputs_th', dtype=th.config.floatX)
        self.random_th = tt.vector(self.name + '_random_th', dtype=th.config.floatX)

        self.space_th.tag.test_value = self.space_values
        self.inputs_th.tag.test_value = self.inputs_values
        self.outputs_th.tag.test_value = self.outputs_values
        self.random_th.tag.test_value = np.random.randn(len(self.space_values)).astype(dtype=th.config.floatX)

        if hidden is None:
            self.hidden = None
        else:
            self.hidden = np.squeeze(hidden)

        # Parametrization
        self.location = location
        if noise:
            self.kernel_f = kernel
            self.kernel = KernelSum(self.kernel_f, WN(self.space_values, 'Noise'))
        else:
            self.kernel_f = kernel
            self.kernel = self.kernel_f
        self.mapping = mapping
        self.freedom = freedom

        with self.model:

            self.location.check_dims(self.inputs_values)
            self.kernel.check_dims(self.inputs_values)
            self.mapping.check_dims(self.outputs_values)

            self.location.check_hypers(self.name + '_')
            self.kernel.check_hypers(self.name + '_')
            self.mapping.check_hypers(self.name + '_')

        print('Space Dimensions: ', self.space_values.shape)

        # Hyper-parameters values
        self._widget_traces = None
        self.params_current = None
        self.params_widget = None
        self.params_fixed = {}

        # Basic Tensors
        self.location_space = self.location(self.space_th)
        self.location_inputs = self.location(self.inputs)

        self.kernel_space = tt_to_cov(self.kernel.cov(self.space_th))
        self.kernel_inputs = tt_to_cov(self.kernel.cov(self.inputs))
        self.kernel_space_inputs = tt_to_num(self.kernel.cov(self.space_th, self.inputs))

        self.kernel_f_space = tt_to_cov(self.kernel_f.cov(self.space_th))
        self.kernel_f_inputs = tt_to_cov(self.kernel_f.cov(self.inputs))
        self.kernel_f_space_inputs = tt_to_num(self.kernel_f.cov(self.space_th, self.inputs))

        self.mapping_outputs = tt_to_num(self.mapping.inv(self.outputs))

        # Prior
        self.prior_mean = None
        self.prior_covariance = None
        self.prior_variance = None
        self.prior_std = None
        self.prior_noise = None
        self.prior_median = None
        self.prior_quantile_up = None
        self.prior_quantile_down = None
        self.prior_noise_up = None
        self.prior_noise_down = None
        self.prior_sampler = None

        # Posterior
        self.posterior_mean = None
        self.posterior_covariance = None
        self.posterior_variance = None
        self.posterior_std = None
        self.posterior_noise = None
        self.posterior_median = None
        self.posterior_quantile_up = None
        self.posterior_quantile_down = None
        self.posterior_noise_up = None
        self.posterior_noise_down = None
        self.posterior_sampler = None

        self.distribution = None

        self.compiles = {}

        self.define_process()
        print('Definition OK')

        self.observed(inputs, outputs)
        self.compile()
        print('Compilation OK')

    def define_process(self):
        pass

    def compile(self):

        params = [self.space_th] + self.model.vars
        self.compiles['location_space'] = makefn(params, self.location_space)
        self.compiles['kernel_space'] = makefn(params, self.kernel_space)
        self.compiles['kernel_f_space'] = makefn(params, self.kernel_f_space)

        params = [self.inputs_th] + self.model.vars
        self.compiles['location_inputs'] = makefn(params, self.location_inputs)
        self.compiles['kernel_inputs'] = makefn(params, self.kernel_inputs)
        self.compiles['kernel_f_inputs'] = makefn(params, self.kernel_f_inputs)

        params = [self.space_th, self.inputs_th] + self.model.vars
        self.compiles['kernel_space_inputs'] = makefn(params, self.kernel_space_inputs)
        self.compiles['kernel_f_space_inputs'] = makefn(params, self.kernel_f_space_inputs)

        params = [self.outputs_th] + self.model.vars
        self.compiles['mapping_outputs'] = makefn(params, self.mapping_outputs)

        params = [self.space_th] + self.model.vars
        self.compiles['prior_mean'] = makefn(params, self.prior_mean)
        self.compiles['prior_covariance'] = makefn(params, self.prior_covariance)
        self.compiles['prior_variance'] = makefn(params, self.prior_variance)
        self.compiles['prior_std'] = makefn(params, self.prior_std)
        self.compiles['prior_noise'] = makefn(params, self.prior_noise)
        self.compiles['prior_median'] = makefn(params, self.prior_median)
        self.compiles['prior_quantile_up'] = makefn(params, self.prior_quantile_up)
        self.compiles['prior_quantile_down'] = makefn(params, self.prior_quantile_down)
        self.compiles['prior_noise_up'] = makefn(params, self.prior_noise_up)
        self.compiles['prior_noise_down'] = makefn(params, self.prior_noise_down)
        self.compiles['prior_sampler'] = makefn([self.random_th] + params, self.prior_sampler)

        params = [self.space_th, self.inputs_th, self.outputs_th] + self.model.vars
        self.compiles['posterior_mean'] = makefn(params, self.posterior_mean)
        self.compiles['posterior_covariance'] = makefn(params, self.posterior_covariance)
        self.compiles['posterior_variance'] = makefn(params, self.posterior_variance)
        self.compiles['posterior_std'] = makefn(params, self.posterior_std)
        self.compiles['posterior_noise'] = makefn(params, self.posterior_noise)
        self.compiles['posterior_median'] = makefn(params, self.posterior_median)
        self.compiles['posterior_quantile_up'] = makefn(params, self.posterior_quantile_up)
        self.compiles['posterior_quantile_down'] = makefn(params, self.posterior_quantile_down)
        self.compiles['posterior_noise_up'] = makefn(params, self.posterior_noise_up)
        self.compiles['posterior_noise_down'] = makefn(params, self.posterior_noise_down)
        self.compiles['posterior_sampler'] = makefn([self.random_th] + params, self.posterior_sampler)

        if False:
            params = self.model.vars
            value, dist = self.marginal_gp()
            dist_gp = makefn([value] + params, dist[index])
            trans = makefn([value] + params, self.mapping(value))
            trans_inv = makefn([value] + params, self.mapping.inv(value))
            det_jac_trans_inv = makefn([value] + params, tt.exp(self.mapping.logdet_dinv(value)))
            value, dist = self.marginal_tgp()
            dist_tgp = makefn([value] + params, dist[index])
            self.compiles['trans'] = trans
            self.compiles['trans_inv'] = trans_inv
            self.compiles['det_jac_trans_inv'] = det_jac_trans_inv
            self.compiles['dist_gp'] = dist_gp
            self.compiles['dist_tgp'] = dist_tgp

    def describe(self, title=None, x=None, y=None, text=None):
        if title is not None:
            self.description['title'] = title
        if title is not None:
            self.description['x'] = x
        if title is not None:
            self.description['y'] = y
        if title is not None:
            self.description['text'] = text

    def set_space(self, space):
        __, self.space_values, self.space_index = def_space(space)

    def observed(self, inputs=None, outputs=None):
        if inputs is None or outputs is None or len(inputs) == 0 or len(inputs) == 0:
            self.inputs_values, self.outputs_values, self.observed_index = None, None, None
            self.inputs.set_value(self.inputs_values)
            self.outputs.set_value(self.outputs_values)
            return

        __, self.inputs_values, self.observed_index = def_space(inputs)
        __, self.outputs_values, __ = def_space(outputs, squeeze=True)
        self.inputs.set_value(self.inputs_values)
        self.outputs.set_value(self.outputs_values)
        if self.distribution is None:
            with self.model:
                self.distribution = TGPDist(self.name, mu=self.location(self.inputs), cov=tt_to_cov(self.kernel.cov(self.inputs)),
                                            mapping=self.mapping, tgp=self, observed=self.outputs, testval=self.outputs, dtype=th.config.floatX)

    def prior(self, params=None, space=None, mean=True, var=True, cov=False, median=False, quantiles=False, noise=False, samples=0):
        if params is None:
            params = self.get_params_current()
        if space is None:
            space = self.space_values
        values = {}
        if mean:
            values['mean'] = self.compiles['prior_mean'](space, **params)
        if var:
            values['variance'] = self.compiles['prior_variance'](space, **params)
            values['std'] = self.compiles['prior_std'](space, **params)
        if cov:
            values['covariance'] = self.compiles['prior_covariance'](space, **params)
        if median:
            values['median'] = self.compiles['prior_median'](space, **params)
        if quantiles:
            values['quantile_up'] = self.compiles['prior_quantile_up'](space, **params)
            values['quantile_down'] = self.compiles['prior_quantile_down'](space, **params)
        if noise:
            values['noise'] = self.compiles['prior_noise'](space, **params)
            values['noise_up'] = self.compiles['prior_noise_up'](space, **params)
            values['noise_down'] = self.compiles['prior_noise_down'](space, **params)
        # TODO: if samples is with another distribution
        if samples > 0:
            S = np.empty((len(space), samples))
            rand = np.random.randn(len(space), samples)
            for i in range(samples):
                S[:, i] = self.compiles['prior_sampler'](rand[:, i], space, **params)
                values['samples'] = S
        return values

    def posterior(self, params=None, space=None, inputs=None, outputs=None, mean=True, var=True, cov=False, median=False, quantiles=False, noise=False, samples=0):
        if params is None:
            params = self.get_params_current()
        if space is None:
            space = self.space_values
        if inputs is None:
            inputs = self.inputs_values
        if outputs is None:
            outputs = self.outputs_values
        values = {}
        if mean:
            values['mean'] = self.compiles['posterior_mean'](space, inputs, outputs, **params)
        if var:
            values['variance'] = self.compiles['posterior_variance'](space, inputs, outputs, **params)
            values['std'] = self.compiles['posterior_std'](space, inputs, outputs, **params)
        if cov:
            values['covariance'] = self.compiles['posterior_covariance'](space, inputs, outputs, **params)
        if median:
            values['median'] = self.compiles['posterior_median'](space, inputs, outputs, **params)
        if quantiles:
            values['quantile_up'] = self.compiles['posterior_quantile_up'](space, inputs, outputs, **params)
            values['quantile_down'] = self.compiles['posterior_quantile_down'](space, inputs, outputs, **params)
        if noise:
            values['noise'] = self.compiles['posterior_noise'](space, inputs, outputs, **params)
            values['noise_up'] = self.compiles['posterior_noise_up'](space, inputs, outputs, **params)
            values['noise_down'] = self.compiles['posterior_noise_down'](space, inputs, outputs, **params)
        # TODO: if samples is with another distribution
        if samples > 0:
            S = np.empty((len(space), samples))
            rand = np.random.randn(len(space), samples)
            for i in range(samples):
                S[:, i] = self.compiles['posterior_sampler'](rand[:, i], space, inputs, outputs, **params)
            values['samples'] = S
        return values

    def sample(self, params=None, space=None, inputs=None, outputs=None, samples=1, prior=False):
        S = self.predict(params=params, space=space, inputs=inputs, outputs=outputs, mean=False, var=False, cov=False, median=False, quantiles=False, noise=False, samples=samples, prior=False)
        return S['samples']

    def predict(self, params=None, space=None, inputs=None, outputs=None, mean=True, var=True, cov=False, median=False, quantiles=False, noise=False, samples=0, prior=False):
        if params is None:
            params = self.get_params_current()
        if space is None:
            space = self.space_values
        if inputs is None:
            inputs = self.inputs_values
        if outputs is None:
            outputs = self.outputs_values
        if prior or self.observed_index is None:
            return self.prior(params=params, space=space, mean=mean, var=var, cov=cov, median=median, quantiles=quantiles, noise=noise, samples=samples)
        else:
            return self.posterior(params=params, space=space, inputs=inputs, outputs=outputs, mean=mean, var=var, cov=cov, median=median, quantiles=quantiles, noise=noise, samples=samples)

    def plot(self, params=None, space=None, inputs=None, outputs=None, mean=True, var=True, cov=False, median=True, quantiles=True, noise=True, samples=0, prior=False,
             data=True, big=None, scores=False, title=None, loc=1):
        values = self.predict(params=params, space=space, inputs=inputs, outputs=outputs, mean=mean, var=var, cov=cov, median=median, quantiles=quantiles, noise=noise, samples=samples, prior=prior)
        if space is not None:
            self.set_space(space)
        if data:
            self.plot_data(big)
        if mean:
            plt.plot(self.space_index, values['mean'], label='Mean')
        if var:
            plt.plot(self.space_index, values['mean'] + 2.0 * values['std'], '--k', alpha=0.2, label='4.0 std')
            plt.plot(self.space_index, values['mean'] - 2.0 * values['std'], '--k', alpha=0.2)
        if cov:
            pass
        if median:
            plt.plot(self.space_index, values['median'], label='Mean')
        if quantiles:
            plt.fill_between(self.space_index, values['quantile_up'], values['quantile_down'], alpha=0.1, label='95%')
        if noise:
            plt.fill_between(self.space_index, values['noise_up'], values['noise_down'], alpha=0.1, label='noise')
        if samples > 0:
            plt.plot(self.space_index, values['samples'], alpha=0.4)
        if title is None:
            title = self.description['title']
        if scores:
            pass
        text_plot(title, self.description['x'], self.description['y'], loc=loc)

    def set_params(self, params):
        self.params_current = params

    def fix_params(self, fixed_params=None):
        if fixed_params is None:
            fixed_params = {}
        self.params_fixed = fixed_params

    @property
    def fixed_vars(self):
        return [t for t in self.model.vars if t.name in self.params_fixed.keys()]

    @property
    def sampling_vars(self):
        return [t for t in self.model.vars if t not in self.fixed_vars]

    def check_params_dims(self, params):
        r = dict()
        for k, v in params.items():
            try:
                r[k] = np.array(v, dtype=th.config.floatX).reshape(self.model[k].tag.test_value.shape)
            except KeyError:
                pass
        return r

    def default_hypers(self):
        x = self.inputs_values
        y = self.outputs_values
        return {**self.location.default_hypers_dims(x, y), **self.kernel.default_hypers_dims(x, y),
                **self.mapping.default_hypers_dims(x, y)}

    def widget_plot(self, params):
        self.params_widget = params
        self.plot(params = self.params_widget)

    def widget_traces(self, traces):
        self._widget_traces = traces
        interact(self.widget_plot_trace, __manual=True, id_trace=[0, len(self._widget_traces) - 1])

    def widget_plot_trace(self, id_trace):
        self.widget_plot(self.check_params_dims(self._widget_traces[id_trace]))

    def widget_plot_params(self, **params):
        self.widget_plot(self.check_params_dims(params))

    def widget_params(self, params=None):
        if params is None:
            params = self.get_params_widget()
        intervals = dict()
        for k, v in params.items():
            v = np.squeeze(v)
            if v > 0.1:
                intervals[k] = [0, 2*v]
            elif v < -0.1:
                intervals[k] = [2*v, 0]
            else:
                intervals[k] = [-5.00, 5.00]
        interact(self.widget_plot_params, __manual=True, **intervals)

    def get_params_default(self, fixed=True):
        if self.observed_index is None:
            return self.model.test_point
        default = {}
        for k, v in trans_hypers(self.default_hypers()).items():
            default[k.name] = v
        if fixed:
            default.update(self.params_fixed)
        return default

    def get_params_current(self, fixed=True):
        if self.params_current is None:
            return self.get_params_default()
        if fixed:
            self.params_current.update(self.params_fixed)
        return clone(self.params_current)

    def get_params_widget(self, fixed=False):
        if self.params_widget is None:
            return self.get_params_default()
        if fixed:
            self.params_widget.update(self.params_fixed)
        return clone(self.params_widget)

    def find_MAP(self, start=None, points=1, plot=False, return_points=False, display=True):
        points_list = list()
        if start is None:
            start = self.get_params_current()
        if self.outputs.get_value() is None:
            print('For find_MAP it is necessary to have observations')
            return start
        points_list.append(('start', self.model.logp(start), start))
        print('Starting function value (-logp): ' + str(-self.model.logp(start)))
        if plot:
            plt.figure(0)
            self.plot(params=start, title='start')
            plt.show()
        with self.model:
            for i in range(points):
                try:
                    name, logp, start = points_list[i // 2]
                    if i % 2 == 0:
                        name += '_bfgs'
                        print('\n' + name)
                        new = pm.find_MAP(fmin=sp.optimize.fmin_bfgs, vars=self.sampling_vars, start=start)
                    else:
                        name += '_powell'
                        print('\n' + name)
                        new = pm.find_MAP(fmin=sp.optimize.fmin_powell, vars=self.sampling_vars, start=start)
                    points_list.append((name, self.model.logp(new), new))
                    if plot:
                        plt.figure(i+1)
                        self.plot(params=new, title=name)
                        plt.show()
                except:
                    pass
        optimal = points_list[0]
        for test in points_list:
            if test[1] > optimal[1]:
                optimal = test
        name, logp, params = optimal
        if display:
            #print(params)
            pass
        if return_points is False:
            return params
        else:
            return params, points_list

    def sample_hypers(self, start=None, samples=1000, chains=1, advi=True):
        if start is None:
            start = self.get_params_current()
        if self.outputs.get_value() is None:
            print('For sample_hypers it is necessary to have observations')
            return start
        with self.model:
            if advi:
                advi_mu, advi_sm, advi_elbo = pm.advi(vars=self.sampling_vars, start=start, n=20000) #OK
                for k, v in advi_sm.items():
                    advi_sm[k] = v**2
            else:
                advi_mu = start
                advi_sm = None
            if len(self.fixed_vars) > 0:
                step = [ConstantStep(vars=self.fixed_vars)]  # Fue eliminado por error en pymc3
                step += [RobustSlice(vars=self.sampling_vars)]  # Slice original se cuelga si parte del óptimo
                #step += [pm.Metropolis(vars=self.sampling_vars, tune=False)] # OK
                #step += [pm.HamiltonianMC(vars=self.sampling_vars, scaling=advi_sm, is_cov=True)] #Scaling is not positive definite. Simple check failed. Diagonal contains negatives. Check indexes
                #step += [pm.NUTS(vars=self.sampling_vars, scaling=advi_sm, is_cov=True)] #BUG float32
            else:
                step = RobustSlice()
            trace = pm.sample(samples, step=step, start=advi_mu, njobs=chains)
        return trace

    def save_model(self, path, params=None):
        if params is None:
            params = self.get_params_current()
        try:
            with self.model:
                with open(path, 'wb') as f:
                    pickle.dump((params, self), f, protocol=-1)
            print('Saved model '+path)
        except:
            print('Error saving model '+path)

    # TODO:
    def plot_space(self, space = None):
        if space is not None:
            self.set_space(space)
        plt.plot(self.space_index, self.space_values)
        if self.observed_index is not None:
            plt.plot(self.observed_index, self.inputs_values, '.k')

    def plot_data(self, big=None):
        if big is None:
            big = config.plot_big
        if big:
            self.plot_data_big()
        else:
            self.plot_data_normal()

    def plot_data_normal(self):
        if self.hidden is not None:
            plt.plot(self.space_index, self.hidden[0:len(self.space_index)], label='Hidden Processes')
        if self.outputs_values is not None:
            plt.plot(self.observed_index, self.outputs_values, '.k', label='Observations')

    def plot_concentration(self):
        return plt.matshow(self.cov_inputs)

    def plot_data_big(self):
        if self.hidden is not None:
            plt.plot(self.space_index, self.hidden[0:len(self.space_index)], linewidth=4, label='Hidden Processes')
        if self.outputs_values is not None:
            plt.plot(self.observed_index, self.outputs_values, '.k', ms=20, label='Observations')

    def marginal(self):
        pass

    def subprocess(self, subkernel, mean=True, cov=False, var=True, median=False, quantiles=False, noise=False):
        pass

    def scores_params(self, params=None):
        try:
            logp_train = np.nanmean(self.model.logp(params))
        except:
            logp_train = np.float32(0)

        mean = self.compiles['m1'](**params)
        var = mean**2 - self.compiles['m2'](**params)
        #print(mean.shape)
        #print(self.outputs.get_value().shape)

        mse_train = 0#np.nanmean((mean - self.outputs.get_value()) ** 2 + var)
        bias_train = 0#np.nanmean(np.abs(mean - self.outputs.get_value()))

        self.swap_test_obs()
        try:
            logp_test = np.nanmean(self.model.logp(params))
        except:
            logp_test = np.float32(0)
        mean = self.compiles['m1'](**params)
        var = mean**2 - self.compiles['m2'](**params)
        mse_test = 0#np.nanmean((mean - self.outputs.get_value()) ** 2 + var)
        bias_test = 0#np.nanmean(np.abs(mean - self.outputs.get_value()))
        self.swap_test_obs()

        d = {'logp_train': logp_train,
             'mse_train': mse_train,
             'mab_train': bias_train,
             'logp_test': logp_test,
             'mse_test': mse_test,
             'mab_test': bias_test}
        return d

    def get_point(self, point):
        return {v.name: point[v.name] for v in self.model.vars}

    def point_to_In(self, point):
        r = list()
        for k, v in point.items():
            r.append(th.In(self.model[k], value=v))
        return r

    def eval_point(self, point):
        r = dict()
        for k, v in point.items():
            r[self.model[k]] = v
        return r

    def eval_default(self):
        return self.eval_point(self.get_params_default())

    def eval_current(self):
        return self.eval_point(self.get_params_current())

    def eval_widget(self):
        return self.eval_point(self.get_params_widget())