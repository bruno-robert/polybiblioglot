from dearpygui.core import *
from dearpygui.simple import *
from math import sin

def on_render(sender, data):
    frame_count = get_data("frame_count")
    frame_count += 1
    add_data("frame_count", frame_count)
    add_scatter_series("A plot", "Sin", [0, 100, frame_count%100], [0, 100, frame_count%33], outline=[0, 255, 0, 100])

with window("Tutorial", width=500, height=500):
    add_plot("A plot", height=-1)
    add_data("frame_count", 0)
    set_render_callback(on_render)

start_dearpygui()
# from matplotlib import pyplot as plt
# import numpy as np
# import mpl_toolkits.mplot3d.axes3d as p3
# from matplotlib import animation
#
# fig = plt.figure()
# ax = p3.Axes3D(fig)
# ax_2 = p3
#
# # create the parametric curve
# t=np.arange(0, 2*np.pi, 2*np.pi/100)
# x=np.cos(t)
# y=np.sin(t)
# z=t/(2.*np.pi)
#
# # create the first plot
# point, = ax.plot([x[0]], [y[0]], [z[0]], 'o')
# # line, = ax.plot(x, y, z, label='parametric curve')
# ax.legend()
# ax.set_xlim([-1.5, 1.5])
# ax.set_ylim([-1.5, 1.5])
# ax.set_zlim([-1.5, 1.5])
#
# # second option - move the point position at every frame
# def update_point(n, x, y, z, point):
#     point.set_data(np.array([x[n], y[n]]))
#     point.set_3d_properties(z[n], 'z')
#     return point
#
# ani=animation.FuncAnimation(fig, update_point, 99, fargs=(x, y, z, point))
#
# plt.show()