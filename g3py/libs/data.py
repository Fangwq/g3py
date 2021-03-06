""" This module contains different data generators.

"""

import g3py as g3
import numpy as np
import pandas as pd
from .plots import plot as g3plot, plot_text, show


def data_sunspots():
    import statsmodels.api as sm
    data = sm.datasets.sunspots.load_pandas().data['SUNACTIVITY']
    print(sm.datasets.sunspots.NOTE)
    x = data.index.values[:]
    y = data.values[:]
    return x, y


def data_co2(source='sklearn'):
    if source is 'sklearn':
        from sklearn.datasets import fetch_mldata
        fetch = fetch_mldata('mauna-loa-atmospheric-co2')
        print(fetch.DESCR)
        x = fetch.data[:, 1]
        y = fetch.data[:, 0]
    else:
        import statsmodels.api as sm
        data = sm.datasets.co2.load_pandas().data
        print(sm.datasets.co2.NOTE)
        x = data.index.values[:]
        y = data.values[:, 0]
    return x, y


def data_engel(dataframe = False):
    import statsmodels.api as sm
    data = sm.datasets.engel.load_pandas().data
    print(sm.datasets.engel.NOTE)
    if dataframe:
        return data
    else:
        return data.index.values, data['income'].values


def data_heart():
    hr = pd.read_csv(g3.__path__[0] + '/libs/datasets/hr2.txt', names=['hr'], dtype=np.float32)
    return hr.index.values, hr.values


def data_eurusd():
    hr = pd.read_csv(g3.__path__[0] + '/libs/datasets/EURUSD-1401-1510.txt', names=['EURUSD'], dtype=np.float32)
    return hr.index.values, hr.values


def data_abalone(dataframe=False, raw=False):
    names = ['Sex', 'Length', 'Diam', 'Height', 'Whole', 'Shucked', 'Viscera', 'Shell', 'Rings']
    print('abalone')
    abalone = pd.read_csv(g3.__path__[0] + '/libs/datasets/abalone.data', names=names)
    if not raw:
        abalone['Sex'] = (abalone['Sex'] == 'M') * 1.0 + (abalone['Sex'] == 'F') * 0.0 + 0.0
    if dataframe:
        return abalone
    else:
        x = abalone.drop('Rings', axis=1).values.astype(dtype=np.float32)
        y = abalone['Rings'].values.astype(dtype=np.float32)
        return x, y


def data_creep(dataframe=False, raw=False):
    names = ['Lifetime', 'Rupture_stress', 'Temperature', 'Carbon', 'Silicon', 'Manganese', \
             'Phosphorus', 'Sulphur', 'Chromium', 'Molybdenum', 'Tungsten', 'Nickel', 'Copper', \
             'Vanadium', 'Niobium', 'Nitrogen', 'Aluminium', 'Boron', 'Cobalt', 'Tantalum', 'Oxygen', \
             'Normalising_temperature', 'Normalising_time', 'Cooling_rate', 'Tempering_temperature', \
             'Tempering_time', 'Cooling_rate_tempering', 'Annealing_temperature', 'Annealing_time', \
             'Cooling_rate_annealing', 'Rhenium']
    print('creep')
    creep = pd.read_table(g3.__path__[0] + '/libs/datasets/creep', names=names).astype('float32')
    if not raw:
        creep = creep.drop(['Tantalum', 'Cooling_rate_annealing', 'Rhenium'], axis=1)
        creep['Rupture_stress'] *= 1e-1
    if dataframe:
        return creep
    else:
        x = creep.drop('Rupture_stress', axis=1).values.astype(dtype=np.float32)
        y = creep['Rupture_stress'].values.astype(dtype=np.float32)
        return x, y


def data_ailerons(dataframe=False, raw=False):
    names = ['climbRate', 'Sgz', 'p', 'q', 'curPitch', 'curRoll', 'absRoll', 'diffClb', 'diffRollRate', \
             'diffDiffClb', 'SeTime1', 'SeTime2', 'SeTime3', 'SeTime4', 'SeTime5', 'SeTime6', 'SeTime7', \
             'SeTime8', 'SeTime9', 'SeTime10', 'SeTime11', 'SeTime12', 'SeTime13', 'SeTime14', \
             'diffSeTime1', 'diffSeTime2', 'diffSeTime3', 'diffSeTime4', 'diffSeTime5', 'diffSeTime6', \
             'diffSeTime7', 'diffSeTime8', 'diffSeTime9', 'diffSeTime10', 'diffSeTime11', \
             'diffSeTime12', 'diffSeTime13', 'diffSeTime14', 'alpha', 'Se', 'goal']
    print('ailerons')
    ailerons = pd.concat([pd.read_csv(g3.__path__[0] + '/libs/datasets/ailerons.data', names=names)]).astype('float32')
                          #pd.read_csv(g3.__path__[0] + '/libs/datasets/ailerons.test', names=names)]).astype('float32')
    if not raw:
        ailerons['goal'] *= 1e4
        ailerons = ailerons.drop(['diffSeTime2', 'diffSeTime4', 'diffSeTime6', 'diffSeTime8', 'diffSeTime10',
                                  'diffSeTime12', 'diffSeTime14'], axis=1)
    if dataframe:
        return ailerons
    else:
        x = ailerons.drop('goal', axis=1).values.astype(dtype=np.float32)
        y = ailerons['goal'].values.astype(dtype=np.float32)
        return x, y


def data_rivers():
    r1 = np.exp(pd.read_csv(g3.__path__[0] + '/libs/datasets/logbmau.csv', names=['bmau'], dtype=np.float32, skiprows=1))
    r2 = np.exp(pd.read_csv(g3.__path__[0] + '/libs/datasets/logbmis.csv', names=['bmis'], dtype=np.float32, skiprows=1))
    r3 = np.exp(pd.read_csv(g3.__path__[0] + '/libs/datasets/logcip.csv', names=['cip'], dtype=np.float32, skiprows=1))
    r4 = np.exp(pd.read_csv(g3.__path__[0] + '/libs/datasets/logcol.csv', names=['col'], dtype=np.float32, skiprows=1))
    r5 = np.exp(pd.read_csv(g3.__path__[0] + '/libs/datasets/logmau.csv', names=['mau'], dtype=np.float32, skiprows=1))
    return pd.concat([r1, r2, r3, r4, r5], axis=1)


def save_csv(df, file, index_col=0):
    return df.to_csv(file, index_col=index_col)


def load_csv(file, index_col=0):
    return pd.read_csv(file, index_col=index_col)


def random_obs(x, y, p=0.2, s=1.0, include_min=False, plot=True, plot_independent=False):
    """Generates a random subsample of size len(x)*s*p from the arrays x and y.
    Args:
        x (array): independent variable
        y (array): dependent data
        p (float): porcentual size of the subsample
        s (float): porcentual size from x to subsample
        include_min (bool): whether include or not the minimun of x.
        plot (bool): to plot the data
        plot_independet (bool): to plot into different figures
    Returns:
        obs_j /array): index of the elements that were subsampled
        x_obs (array): set of elements of x that were subsampled.
        y_obs (array): set of elements of y that were subsampled.
        test_j (array): index of the elements that weren't subsampled.
        x_test (array): set of elements of x that weren't subsampled.
        x_test (array): set of elements of y that weren't subsampled.
        """


    n = int(len(x)*s)
    obs_j = np.unique(np.sort(np.random.choice(range(n), int(n*p), replace=False)))
    if include_min:
        id_min = y.argmin()
        if id_min not in obs_j:
            obs_j[np.random.choice(range(int(n*p)), 1)] = id_min
            obs_j = np.sort(obs_j)
    test_j = np.array([v for v in np.arange(len(x)) if v not in obs_j])
    x_obs = x[obs_j]
    y_obs = y[obs_j]
    x_test = x[test_j]
    y_test = y[test_j]
    print('Total: '+str(len(x)) +' | '+'Obs: '+str(len(obs_j)) + ' ('+str(100*len(obs_j)/len(x))+'%)')
    if plot:
        if len(x.shape) > 1:
            id = np.arange(len(x))

            g3plot(id, y)
            g3plot(obs_j, y_obs, '.k', ms=20)
            g3plot(obs_j, y_obs, '.r', ms=15, label='Observations')
            plot_text('Output', '', 'y', legend=True)
            show()

            if plot_independent:
                for k in range(x.shape[1]):
                    g3plot(id, x[:, k])
                    g3plot(obs_j, x_obs[:, k], '.k', ms=20)
                    g3plot(obs_j, x_obs[:, k], '.r', ms=15, label='Observations')
                    plot_text('Input '+str(k), '', 'x', legend=True)
                    show()
            else:
                g3plot(id, x)
                g3plot(obs_j, x_obs, '.k', ms=20)
                g3plot(obs_j, x_obs, '.r', ms=15)
                plot_text('Inputs', '', 'x', legend=False)
                show()
        else:
            g3plot(x, y)
            g3plot(x_obs, y_obs, '.k', ms=20)
            g3plot(x_obs, y_obs, '.r', ms=15, label='Observations')
            plot_text('Data', 'Inputs', 'Outputs', legend=True)
    return obs_j, x_obs, y_obs, test_j, x_test, y_test


def uniform_obs(x, y, p=0.2, s=1.0, plot=True):
    n = int(len(x) * s)
    obs_j = np.arange(0, n, int(1/p)).astype(np.int)
    test_j = np.array([v for v in np.arange(len(x)) if v not in obs_j])
    x_obs = x[obs_j]
    y_obs = y[obs_j]
    x_test = x[test_j]
    y_test = y[test_j]
    print('Total: '+str(len(x)) +' | '+'Obs: '+str(len(obs_j)) + ' ('+str(100*len(obs_j)/len(x))+'%)')
    if plot:
        g3plot(x, y)
        g3plot(x_obs, y_obs, '.k', ms=20)
        g3plot(x_obs, y_obs, '.r', ms=15, label='Observations')
        plot_text('Data', 'X', 'Y', legend=True)
    return obs_j, x_obs, y_obs, test_j, x_test, y_test
