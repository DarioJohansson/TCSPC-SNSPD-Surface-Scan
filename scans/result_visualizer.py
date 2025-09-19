import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from scans.scan_data_structures import *
from matplotlib.ticker import FuncFormatter
from functools import partial
from datetime import datetime

def interactive_1D_graph(results, settings):
    axis = results.active_axes[0]

    fig, ax = plt.subplots()
    ax.grid(color="black", linestyle="--", alpha=0.6)
    ax.set_xlabel(f"{axis} position µm (lab ref. frame)")
    ax.set_ylabel(f"Photon incidence frequency (Hz)")
    X_data = [i for i in range(results.resolution[axis])]
    Y_data = []
    to_physical = lambda i: round(i * settings.step_size[axis] * 1e6, 9)
    formatter = FuncFormatter(lambda i, _: to_physical(i))
    ax.xaxis.set_major_formatter(formatter)

    for idx in np.ndindex(results.data_dims):
        Y_data.append(results.get_data(idx, CountData).frequency())
    
    def show_tol_graph(event):
        def update_annot(ev, obj, annot, _fig, _ax):
            if ev.inaxes == _ax:
                if ev.key == "control":
                    # nearest index in obj.x_data
                    idx = np.searchsorted(obj.x_data, ev.xdata)
                    if 0 <= idx < len(obj.x_data):
                        annot.xy = (obj.x_data[idx], obj.y_data[idx])
                        text = f"x={obj.x_data[idx]} (ps), y={obj.y_data[idx]:.2f}"
                        annot.set_text(text)
                        annot.set_visible(True)
                        _fig.canvas.draw_idle()
            else:
                annot.set_visible(False)
                _fig.canvas.draw_idle()
        
        if event.inaxes == ax:
            col = int(round(event.xdata))
            if 0 <= col < results.resolution[axis]:
                obj = results.get_data((col,), ToLData)
                count_obj = results.get_data((col,), CountData)
                _fig,_ax = plt.subplots()
                annot = _ax.annotate(
                    "", xy=(0,0), xytext=(15,15), textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->")
                )
                annot.set_visible(False)
                _ax.plot(obj.x_data, obj.y_data, drawstyle="steps-mid")
                _ax.set_title(f"Position: {to_physical(col)} (µm)\nPhoton Frequency: {count_obj.frequency()} (Hz)\nTimestamp Delay: {settings.tol_delay} (ps)\nTime Acquired: {datetime.fromtimestamp(obj.time_created)}", fontsize=10, fontweight="bold")
                _ax.set_xlabel("Time from start signal + delay (ps)", fontsize=10)
                _ax.set_ylabel("Counts per bin", fontsize=10)
                _ax.grid(True, linestyle="--", alpha=0.6)
                _fig.canvas.mpl_connect("motion_notify_event", partial(update_annot, obj=obj, annot=annot, _fig=_fig, _ax=_ax))
                _fig.show()

            else:
                raise ValueError(f"Out of bounds: {col}")

    fig.canvas.mpl_connect("button_press_event", show_tol_graph)
    ax.plot(X_data, Y_data)
    plt.show()

def interactive_2D_grid(results, settings):
    axes = results.active_axes
    rows,cols = results.data_dims
    
    fig, ax = plt.subplots()
    ax.set_xticks(np.arange(cols + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(rows + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.set_xlabel(f"{axes[0]} position (lab ref. frame)")
    ax.set_ylabel(f"{axes[1]} position (lab ref. frame)")
    ax.set_xticks([])
    ax.set_yticks([])

    # Setting up the scaling for the two dimensions.
    to_physical_rows_fn = lambda x: x*(settings.step_size[axes[0]]*1e6)
    norm_rows_fn = lambda u: u/(settings.step_size[axes[0]]*1e6)

    to_physical_cols_fn = lambda y: y*(settings.step_size[axes[1]]*1e6)
    norm_cols_fn = lambda u: u/(settings.step_size[axes[1]]*1e6)

    # Create a second axis on top and right
    ax_top = ax.secondary_xaxis("top", functions=(to_physical_rows_fn, norm_rows_fn))
    ax_right = ax.secondary_yaxis("right", functions=(to_physical_cols_fn, norm_cols_fn))

    ax_top.set_xlabel(f"{axes[0]} [µm]")
    ax_right.set_ylabel(f"{axes[1]} [µm]")
    annot = ax.annotate(
        "", xy=(0,0), xytext=(15,15), textcoords="offset points",
        bbox=dict(boxstyle="round", fc="w"),
        arrowprops=dict(arrowstyle="->")
    )
    annot.set_visible(False)

    # Annotation function:
    def update_grid_annot(ev, obj, annot, _fig, _ax):
        if ev.inaxes == _ax:
            if ev.key == "control":
                row = int(round(ev.xdata))
                col = int(round(ev.ydata))
                if 0 <= row < rows and 0 <= col < cols:
                    annot.xy = (row, col)
                    text = f"{axes[0]}={to_physical_rows_fn(row)} (µm), {axes[1]}={to_physical_cols_fn(col)} (µm)"
                    annot.set_text(text)
                    annot.set_visible(True)
                    _fig.canvas.draw_idle()
        else:
            annot.set_visible(False)
            _fig.canvas.draw_idle()



    # color function
    min_freq=None
    max_freq=None
    def color_fn(v):
        norm = mcolors.Normalize(vmin=min_freq, vmax=max_freq)
        cmap = plt.cm.gray
        return cmap(norm(v))
    
    # Calculate max and min frequencies with stupid sorting alg (not optimised, i'm not a computer scientist.)
    for idx in np.ndindex(results.data_dims):
        freq = results.get_data(idx, CountData).frequency()
        if min_freq == None:
            min_freq = max_freq = freq
        elif freq < min_freq:
            min_freq = freq
        elif freq > max_freq:
            max_freq = freq

    # Draw colored squares
    for idx in np.ndindex(results.data_dims):
        rect = plt.Rectangle((idx[0] - 0.5, idx[1] - 0.5), 1, 1,
                                facecolor=color_fn(results.get_data(idx, CountData).frequency()),
                                edgecolor="black")
        ax.add_patch(rect)
        #ax.text(j, i, f"{str(results[i, j])}\n{results.get_data((i,j), CountData).frequency()}", va='center', ha='center', color="red")

    def show_tol_graph(event):
        def update_annot(ev, obj, annot, _fig, _ax):
            if ev.inaxes == _ax:
                if ev.key == "control":
                    # nearest index in obj.x_data
                    idx = np.searchsorted(obj.x_data, ev.xdata)
                    if 0 <= idx < len(obj.x_data):
                        annot.xy = (obj.x_data[idx], obj.y_data[idx])
                        text = f"x={obj.x_data[idx]} (ps), y={obj.y_data[idx]:.2f}"
                        annot.set_text(text)
                        annot.set_visible(True)
                        _fig.canvas.draw_idle()
            else:
                annot.set_visible(False)
                _fig.canvas.draw_idle()

        if event.inaxes == ax:
            col = int(round(event.xdata))
            row = int(round(event.ydata))
            index = (row,col)
            if 0 <= row < rows and 0 <= col < cols:
                count_obj =  results.get_data(index, CountData)
                tol_obj = results.get_data(index, ToLData)
                _fig,_ax = plt.subplots()
                annot = _ax.annotate(
                    "", xy=(0,0), xytext=(15,15), textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="->")
                )
                annot.set_visible(False)
                _ax.plot(tol_obj.x_data, tol_obj.y_data, drawstyle="steps-mid")
                _ax.set_title(f"Position: {axes[0]}={to_physical_rows_fn(row)}(µm) {axes[1]}={to_physical_cols_fn(col)}(µm)\nPhoton Frequency: {count_obj.frequency()} (Hz)\nTimestamp Delay: {settings.tol_delay} (ps)\nTime Acquired: {datetime.fromtimestamp(tol_obj.time_created)}", fontsize=10, fontweight="bold")
                _ax.set_xlabel("Time from start signal + delay (ps)", fontsize=10)
                _ax.set_ylabel("Counts per bin", fontsize=10)
                _ax.grid(True, linestyle="--", alpha=0.6)
                _fig.canvas.mpl_connect("motion_notify_event", partial(update_annot, obj=tol_obj, annot=annot, _fig=_fig, _ax=_ax))
                _fig.show()

            else:
                raise ValueError("Out of bounds.")


    fig.canvas.mpl_connect("button_press_event", show_tol_graph)
    fig.canvas.mpl_connect("motion_notify_event", partial(update_grid_annot, obj=results, annot=annot, _fig=fig, _ax=ax))
    plt.gca().invert_yaxis()
    plt.show()


if __name__ == "__main__":

    results = ScanResults.load("results\\scan-10x10-tol.json")
    settings = ScanParameters.load("results\\scan-10x10-tol-settings.json")

    if len(results.data_dims) == 1:
        interactive_1D_graph(results,settings)
    elif len(results.data_dims) == 2:
        interactive_2D_grid(results, settings)
