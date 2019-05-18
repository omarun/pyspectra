"""
SpectraSet
---------
TODO:
"""
import warnings
import numpy as np
import pandas as pd


__all__ = ["Spectra", "rbind"]

class Spectra():
    """ TODO:
    Parameters
    ----------
    Examples
    --------
    See also
    --------
    """
    def __init__(self, spc=None, wl=None, data=None, labels=None, description=None):

        # Parse spc and wl
        if spc is None and wl is None:
            raise ValueError('At least one of spc or wl must be provided!')

        # Prepare SPC
        if spc is not None:
            if isinstance(spc, list) or isinstance(spc, tuple):
                spc = np.array(spc)

            if isinstance(spc, np.ndarray):
                if spc.ndim == 1:
                    spc = pd.DataFrame(spc.reshape(1, len(spc)))
                elif spc.ndim == 2:
                    spc = pd.DataFrame(spc)
                else:
                    raise ValueError('Incorrect spc is provided!')

            if isinstance(spc, pd.Series):
                spc = pd.DataFrame(spc).T
        else:
            spc = pd.DataFrame(columns=pd.Float64Index(wl))

        # Prepare wl
        if wl is None:
            if isinstance(spc, pd.DataFrame) and isinstance(spc.columns, pd.Float64Index):
                wl = spc.columns
            else:
                warnings.warn('Wavelength is not provided: using range 0:ncol(spc) instead.')
                wl = list(range(spc.shape[1]))

        # Combine spc and wl
        spc.columns = pd.Float64Index(wl)
        #spc = spc.reindex(sorted(spc.columns), axis="columns", copy=False)
        self.spc = spc

        # Parse data
        if data is None:
            data = pd.DataFrame(index=range(self.spc.shape[0]))
        elif isinstance(data, dict):
            data = pd.DataFrame(data)
        self.data = data

        # Parse labels
        if labels:
            if isinstance(labels, dict) and labels.get('x', False) and labels.get('y', False):
                self.labels = {'x': labels.x, 'y':labels.y}
            elif (isinstance(labels, tuple) or isinstance(labels, list)) and (len(labels) == 2):
                self.labels = {'x': labels[0], 'y': labels[1]}
            else:
                raise ValueError('Incorrect labels type!')
        else:
            self.labels = {'x': None, 'y': None}

        # Add description if provided
        self.description = description

        # Checks
        #if self.spc.shape[1] != len(self.wl):
        #    raise ValueError('length of wavelength must be equal to number of columns in spc!')
        if self.spc.shape[0] != self.data.shape[0]:
            raise ValueError('data must have the same number of instances(rows) as spc has!')
        
        # Reset indexes to make them the same
        self.spc.reset_index(drop=True, inplace=True)
        self.data.reset_index(drop=True, inplace=True)
    
    @property
    def wl(self):
        """
        Return wavelengths
        """
        return self.spc.columns.values

    @property
    def shape(self):
        """
        Return a tuple representing the dimensionality of the Spectra.
        """
        return self.spc.shape[0], self.spc.shape[1], self.data.shape[1]

    @property
    def nwl(self):
        """
        Return number of wavelenght points.
        """
        return self.spc.shape[1]
    
    @property
    def nspc(self):
        """
        Return number of spectra.
        """
        return self.spc.shape[0]
    
    def _parse_string_or_column_param(self, param):
        if isinstance(param, str) and (param in self.data.columns):
            return self.data[param]
        elif isinstance(param, pd.Series) and (param.shape[0] == self.nspc):
            return param
        elif isinstance(param, np.ndarray) and (param.ndim == 1) and (param.shape[0] == self.nspc):
            return pd.Series(param)
        elif isinstance(param, (list, tuple)) and (len(param) == self.nspc):
            return pd.Series(param)
        else:
            raise TypeError('Incorrect parameter. It must be either a string of a data column name or pd.Series / np.array / list / tuple of lenght equal to number of spectra.')
       
    def plot(self, columns=None, rows=None, color=None, palette=None, fig=None, sharex=False, sharey=False, legend_params={}, **kwds):
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        # Prepare columns and rows
        if rows is None:
            row = pd.Series(np.repeat('dummy', self.nspc), dtype='category')
        else:
            row = self._parse_string_or_column_param(rows).cat.remove_unused_categories()
        row = row.cat.add_categories('NA').fillna('NA').cat.remove_unused_categories()
        
        if columns is None:
            col = pd.Series(np.repeat('dummy', self.nspc), dtype='category')
        else:
            col = self._parse_string_or_column_param(columns)
        col = col.cat.add_categories('NA').fillna('NA').cat.remove_unused_categories()

        nrows = len(row.cat.categories)
        ncols = len(col.cat.categories)

        # Prepare colors
        if color is None:
            labels = pd.Series(['spc']*self.nspc)
        else:
            labels = (self._parse_string_or_column_param(color)
                .cat.add_categories('NA').fillna('NA')
                .cat.remove_unused_categories()
                )
        ncolors = len(labels.cat.categories)
        if palette is None:
            palette = plt.rcParams['axes.prop_cycle'].by_key()['color']
        colors = (labels
            .cat.rename_categories(dict(zip(labels.cat.categories, palette[:ncolors])))
            .cat.add_categories('gray').fillna('gray')
            )

        if fig is None:
            fig = plt.figure()

        fig, ax = plt.subplots(
            nrows, ncols,
            sharex=sharex, sharey=sharey,
            num=fig.number, clear=True,
            squeeze=False
            )
        
        legend_lines = [ Line2D([0], [0], color=c, lw=4) for c in colors.cat.categories ]
        for i, vrow in enumerate(row.cat.categories):
            for j, vcol in enumerate(col.cat.categories):
                rowfilter = (row == vrow) & (col == vcol)
                if np.any(rowfilter):
                    (self.spc
                        .loc[rowfilter, :]
                        .T
                        .plot
                        .line(ax=ax[i, j], color=colors[rowfilter], **kwds)
                        )
                ax[i, j].legend(legend_lines, labels.cat.categories, **legend_params)
                if (i == 0) and (columns is not None):
                    ax[i, j].set_title(str(vcol), fontsize='16', color='black')
                if (j == 0) and (rows is not None):
                    ax[i, j].set_ylabel(str(vrow), fontsize='16', color='black')
        return fig

    # TODO: add a parameter 'inplace' like in pandas
    def smooth(self, how, w, inplace=False, **kwds):
        if not (w % 2):
            raise ValueError("The window size must be an odd number.")
        if w < 3:
            raise ValueError("The window size is too small.")
        if self.nwl < w:
            raise ValueError("The window size is bigger than number of wl points.")

        if how == "savgol":
            from scipy.signal import savgol_filter
            newspc = pd.DataFrame(
                savgol_filter(self.spc.values, w, **kwds, axis=1, mode='constant', cval=np.nan),
                columns=self.spc.columns
                )
        elif how == "mean":
            newspc = self.spc.rolling(w, axis=1, center=True).mean()
        elif how == "median":
            newspc = self.spc.rolling(w, axis=1, center=True).median()
        
        if inplace:
            self.spc = newspc
            return self
        return Spectra(spc=newspc, data=self.data)



    def __getitem__(self, given):
        if (type(given) == tuple) and (len(given) == 3):
            rows, cols, wls = ([x] if (np.size(x) == 1) and (not isinstance(x, (slice,list,tuple))) else x for x in given)
            idx = pd.IndexSlice
            return Spectra(spc=self.spc.loc[rows, idx[wls]], data=self.data.loc[rows, cols])
        else:
            raise ValueError('Incorrect subset value. Provide 3 values in format <row, column, wl>.')

    def __str__(self):
        return str(self.shape)
"""
    def __iter__(self):
        pass
    # -----------------------------------------------------------------------
    # Arithmetic operations +, -, *, /, **, abs
    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __mul__(self, other):
        pass

    def __truediv__(self, other):
        pass

    def __pow__(self, other[, modulo]):
        pass

    def __radd__(self, other):
        pass

    def __rsub__(self, other):
        pass

    def __rmul__(self, other):
        pass

    def __rtruediv__(self, other):
        pass

    def __iadd__(self, other):
        pass

    def __isub__(self, other):
        pass

    def __imul__(self, other):
        pass

    def __itruediv__(self, other):
        pass

    def __abs__(self):
        pass
"""


# TODO: Move from here to a separate module
def rbind(*objs, join="strict", data_join=None, spc_join=None):
    if data_join is None:
        data_join = join
    if spc_join is None:
        spc_join = join

    allowed_joins = ("strict", "outer", "inner")
    if (spc_join not in allowed_joins) or (data_join not in allowed_joins):
        raise ValueError("Incorrect join strategy")
    if len(objs) <= 1:
        raise ValueError("No data to bind.")
    
    if spc_join == "strict":
        for obj in objs:
            if not np.array_equal(obj.wl, objs[0].wl):
                raise ValueError("Strict join is not possible: Spectra have different wavelenghts.")
        spc_join = "outer"
        
    if data_join == "strict":
        for obj in objs:
            if not np.array_equal(obj.data.columns, objs[0].data.columns):
                raise ValueError("Strict join is not possible: Data have different columns.")
        data_join = "outer"

    return Spectra(
        spc=pd.concat([obj.spc for obj in objs], join=spc_join),
        data=pd.concat([obj.data for obj in objs], join=data_join)
    )