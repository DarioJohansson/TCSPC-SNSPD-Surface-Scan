import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

x = np.linspace(0, 2*np.pi, 200)
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
line, = ax.plot(x, np.sin(x))

def to_sin(event):
    line.set_ydata(np.sin(x))
    fig.canvas.draw_idle()

def to_cos(event):
    line.set_ydata(np.cos(x))
    fig.canvas.draw_idle()

# Button areas (fractions of figure size)
ax1 = plt.axes([0.3, 0.05, 0.1, 0.075])
ax2 = plt.axes([0.5, 0.05, 0.1, 0.075])

b1 = Button(ax1, "Sin")
b2 = Button(ax2, "Cos")
b1.on_clicked(to_sin)
b2.on_clicked(to_cos)

plt.show()
