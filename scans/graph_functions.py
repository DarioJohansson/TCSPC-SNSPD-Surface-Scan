import numpy as np
import matplotlib.pyplot as plt
from devices.idq_tc1000_device import *
from matplotlib.widgets import Button
from functools import partial
from datetime import datetime

# # ToL popup render and format functions

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

def to_normal(event, ax, fig):
    ax.set_yscale("linear")
    fig.canvas.draw_idle()
def to_log(event, ax, fig):
    ax.set_yscale("log")
    fig.canvas.draw_idle()

def on_resize(event, ax, fig, left_pos):
    fig_w, fig_h = fig.get_size_inches()*fig.dpi  # figure size in pixels
    # new axes in figure fraction to keep pixel width/height
    height_px = 40
    top_margin_px = 10
    width_px = 100
    left_px = left_pos

    ax.set_position([
        left_px/fig_w,
        1 - (top_margin_px + height_px)/fig_h,  # bottom = 1 - (top + height)
        width_px/fig_w,
        height_px/fig_h
    ])
    fig.canvas.draw_idle()
            

active_figs=[]
def show_tol_graph(
        event, 
        ax, 
        results,
        settings, 
        row_scale_fn, 
        col_scale_fn, 
        axes
        ):
    rows, cols = results.data_dims

    if event.inaxes == ax:
        col = int(round(event.xdata))
        row = int(round(event.ydata))
        index = (row,col)
        if 0 <= row < rows and 0 <= col < cols:
            count_obj =  results.get_data(index, CountData)
            tol_obj = results.get_data(index, ToLData)
            _fig,_ax = plt.subplots()

            ax1 = plt.axes([0.05, 0.9, 0.13, 0.075])  # left, bottom, width, height
            ax2 = plt.axes([0.20, 0.9, 0.13, 0.075])
            
            b1 = Button(ax1, "Linear Scale")
            b2 = Button(ax2, "Log Scale")
            b1.on_clicked(partial(to_normal, ax=_ax, fig=_fig))
            b2.on_clicked(partial(to_log, ax=_ax, fig=_fig))

            annot = _ax.annotate(
                "", xy=(0,0), xytext=(15,15), textcoords="offset points",
                bbox=dict(boxstyle="round", fc="w"),
                arrowprops=dict(arrowstyle="->")
            )
            annot.set_visible(False)
            _ax.set_yscale("linear")
            _ax.plot(tol_obj.x_data, tol_obj.y_data, drawstyle="steps-mid")
            _ax.set_title(f"Position: {axes[0]}={row_scale_fn(row)}(µm) {axes[1]}={col_scale_fn(col)}(µm)\nPhoton Frequency: {count_obj.frequency()} (Hz)\nTimestamp Delay: {settings.tol_delay} (ps)\nTime Acquired: {datetime.fromtimestamp(tol_obj.time_created)}", fontsize=10, fontweight="bold")
            _ax.set_xlabel("Time from start signal + delay (ps)", fontsize=10)
            _ax.set_ylabel("Counts per bin", fontsize=10)
            _ax.grid(True, linestyle="--", alpha=0.6)
            _fig.canvas.mpl_connect("motion_notify_event", partial(update_annot, obj=tol_obj, annot=annot, _fig=_fig, _ax=_ax))
            _fig.canvas.mpl_connect("resize_event", partial(on_resize, ax=ax1, fig=_fig, left_pos=20))
            _fig.canvas.mpl_connect("resize_event", partial(on_resize, ax=ax2, fig=_fig, left_pos=130))
            _fig.show()
            active_figs.append((_fig, _ax, b1, b2))
        else:
            raise ValueError("Out of bounds.")