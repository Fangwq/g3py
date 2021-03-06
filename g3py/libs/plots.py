import os
import IPython.display as display
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sb
from g3py import config
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


def figure(*args, **kwargs):
    return plt.figure(*args, **kwargs)


def plot(*args, **kwargs):
    return plt.plot(*args, **kwargs)


def subplot(*args, **kwargs):
    return plt.subplot(*args, **kwargs)


def tight_layout(*args, **kwargs):
    plt.tight_layout(*args, **kwargs)


def show(*args, **kwargs):
    plt.show(*args, **kwargs)


def style_seaborn():
    """
    This function set some features of the figures.
    """
    plt.style.use('classic')
    sb.set(style='darkgrid', color_codes=False)
    plt.style.use('seaborn-darkgrid')
    plt.rcParams['figure.figsize'] = (20, 6)  #figure size
    config.plot_big = False


def style_normal():
    plt.style.use('classic')
    sb.set(style="white", color_codes=True) #white background
    plt.style.use('seaborn-white')
    plt.rcParams['figure.figsize'] = (20, 6)  #figure size
    plt.rcParams['axes.titlesize'] = 20  # title size
    plt.rcParams['axes.labelsize'] = 18  # xy-label size
    plt.rcParams['xtick.labelsize'] = 16 #x-numbers size
    plt.rcParams['ytick.labelsize'] = 16 #y-numbers size
    plt.rcParams['legend.fontsize'] = 18  # legend size
    #plt.rcParams['legend.fancybox'] = True
    config.plot_big = False


def style_big():
    style_normal()
    plt.rcParams['xtick.labelsize'] = 36  # x-numbers size
    plt.rcParams['ytick.labelsize'] = 36  # x-numbers size
    plt.rcParams['axes.labelsize'] = 36  # xy-label size
    plt.rcParams['axes.titlesize'] = 36  # xy-label size
    plt.rcParams['legend.fontsize'] = 30  # legend size
    config.plot_big = True


def style_big_seaborn():
    """
    It defines the features for the figure for plotting, using the seaborn style.
    """
    style_seaborn()
    plt.rcParams['xtick.labelsize'] = 36  # x-numbers size
    plt.rcParams['ytick.labelsize'] = 36  # x-numbers size
    plt.rcParams['axes.labelsize'] = 36  # xy-label size
    plt.rcParams['axes.titlesize'] = 36  # xy-label size
    plt.rcParams['legend.fontsize'] = 30  # legend size
    config.plot_big = True


def style_text(size=36):
    plt.rcParams['legend.fontsize'] = size  # legend size


def style_widget():
    return display.display(display.HTML('''<style>
                .widget-label { min-width: 30ex !important; }
                .widget-hslider { min-width:100%}
                div.output_subarea {max-width: 100%}
            </style>'''))


def plot_text(title="title", x="xlabel", y="ylabel", ncol=3, loc='best', axis=None, legend=True):
    plt.axis('tight')
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    if legend:
        plt.legend(ncol=ncol, loc=loc)
    if axis is not None:
        plt.axis(axis)


def plot_save(file='example.pdf'):
    os.makedirs(file[:file.rfind('/')], exist_ok=True)
    plt.savefig(file, bbox_inches='tight')


def plot_img(name='example', path='plots/', extension='png', return_html=False):
    file = path + name+'.'+extension
    os.makedirs(file[:file.rfind('/')], exist_ok=True)
    plt.savefig(file, bbox_inches='tight')
    plt.close()
    html = '<img src=\'{}?{}\'>'.format(file, np.random.rand())
    if return_html:
        return html
    display.display(display.HTML(html))


def show_img(name='example', path='plots/', extension='png', return_html=False):
    file = path + name+'.'+extension
    html = '<img src=\'{}?{}\'>'.format(file, np.random.rand())
    if return_html:
        return html
    display.display(display.HTML(html))


def plot_matrix(matrix, color=True, cmap=cm.seismic, figsize=(6, 6)):
    if color:
        if figsize is not None:
            plt.figure(None, figsize)
        v = np.max(np.abs(matrix))
        plt.imshow(matrix, cmap=cmap, vmax=v, vmin=-v)
        ax = plt.gca()
        ax.grid(linewidth=0)

    else:
        plt.matshow(matrix)


def grid2d(x, y):
    xy = np.zeros((len(x) * len(y), 2))
    for i in range(len(x)):
        for j in range(len(y)):
            xy[i * len(y) + j, :] = x[i], y[j]
    x2d, y2d = np.meshgrid(x, y)
    x2d = x2d.T
    y2d = y2d.T
    return xy, x2d, y2d


def plot_2d(xy, x, y, title=None, grid=True, ax=None, contour_z=True, contour_xy=False):
    fxy2d_hidden = xy.reshape((len(x), len(y)))
    if grid:
        x2d, y2d = x, y
    else:
        x2d, y2d = np.meshgrid(x, y)
        x2d, y2d = x2d.T, y2d.T
    if ax is None:
        fig = plt.figure(figsize=[20, 10])
        ax = fig.gca(projection='3d')

    if contour_z:
        cset = ax.contour(x2d, y2d, fxy2d_hidden, zdir='z', offset=np.min(fxy2d_hidden), cmap=cm.RdBu_r)
    if contour_xy:
        cset = ax.contour(x2d, y2d, fxy2d_hidden, zdir='x', offset=np.min(x), cmap=cm.RdBu_r)
        cset = ax.contour(x2d, y2d, fxy2d_hidden, zdir='y', offset=np.max(y), cmap=cm.RdBu_r)

    ax.plot_surface(x2d, y2d, fxy2d_hidden, alpha=0.4, cmap=cm.RdBu_r, rstride=1, cstride=1)
    if title is not None:
        plt.title(title)