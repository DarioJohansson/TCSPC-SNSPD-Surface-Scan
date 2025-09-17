import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from scans.scan_data_structures import *


def interactive_1D_graph(results, settings):
    axis = results.active_axes[0]

    fig, ax = plt.subplots()
    ax.grid(color="black", linestyle="--", alpha=0.6)
    ax.set_xlabel(f"{axis} position (lab ref. frame)")
    ax.set_ylabel(f"Photon incidence frequency (Hz)")
    X_data = None
    Y_data = None

    for i in range(settings.resolution[axis]):
        X_data.append(i*settings.step_size[axis])
    
    for idx in np.ndindex(results.data_dims):
        Y_data.append(results.get_data(idx, CountData).frequency())
    
    def show_tol_graph(event):
        if event.inaxes == ax:
            col = int(round(event.xdata))
            if 0 <= col < results.resolution[axis]:
                obj = results.get_data((col,), ToLData)
                _fig,_ax = plt.subplots()
                _ax.plot(obj.x_data, obj.y_data)
                _ax.set_title(f"Position: {col}", fontsize=13, fontweight="bold")
                _ax.set_xlabel("Time from start signal + delay (ps)", fontsize=10)
                _ax.set_ylabel("Counts per bin", fontsize=10)
                _ax.grid(True, linestyle="--", alpha=0.6)
                _fig.show()

            else:
                raise ValueError("Out of bounds.")

    fig.canvas.mpl_connect("button_press_event", show_tol_graph)
    fig.show()

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
    scale_rows = settings.step_size[axes[0]]*1e6
    scale_cols = settings.step_size[axes[1]]*1e6

    # Create a second axis on top and right
    ax_top = ax.secondary_xaxis("top", functions=(lambda x: x*scale_rows, lambda u: u/scale_rows))
    ax_right = ax.secondary_yaxis("right", functions=(lambda y: y*scale_cols, lambda u: u/scale_cols))

    ax_top.set_xlabel(f"{axes[0]} [µm]")
    ax_right.set_ylabel(f"{axes[1]} [µm]")

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
        if event.inaxes == ax:
            col = int(round(event.xdata))
            row = int(round(event.ydata))
            index = (row,col)
            if 0 <= row < rows and 0 <= col < cols:
                count_obj =  results.get_data(index, CountData)
                tol_obj = results.get_data(index, ToLData)
                _fig,_ax = plt.subplots()
                _ax.plot(tol_obj.x_data, tol_obj.y_data)
                _ax.set_title(f"Position: {axes[0]}={row*scale_rows}µm {axes[1]}={col*scale_cols}µm\nPhoton Frequency: {count_obj.frequency()}", fontsize=13, fontweight="bold")
                _ax.set_xlabel("Time from start signal + delay (ps)", fontsize=10)
                _ax.set_ylabel("Counts per bin", fontsize=10)
                _ax.grid(True, linestyle="--", alpha=0.6)
                _fig.show()

            else:
                raise ValueError("Out of bounds.")


    fig.canvas.mpl_connect("button_press_event", show_tol_graph)
    plt.gca().invert_yaxis()
    plt.show()


if __name__ == "__main__":

    results = ScanResults.load("bidim-scan-tol-2x2.json")
    settings = ScanParameters.load("bidim-scan-tol-2x2-settings.json")

    if len(results.data_dims) == 1:
        interactive_1D_graph(results,settings)
    elif len(results.data_dims) == 2:
        interactive_2D_grid(results, settings)
