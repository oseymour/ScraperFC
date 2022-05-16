import matplotlib.pyplot as plt
from   matplotlib.patches import Arc
import numpy as np
import pandas as pd
import traceback


def plot_field(ax):
    """ Taken from https://fcpython.com/visualisation/drawing-pass-map-python """
    #Pitch Outline & Centre Line
    ax.plot([0,0],[0,90], color="black")
    ax.plot([0,130],[90,90], color="black")
    ax.plot([130,130],[90,0], color="black")
    ax.plot([130,0],[0,0], color="black")
    ax.plot([65,65],[0,90], color="black")

    #Left Penalty Area
    ax.plot([16.5,16.5],[65,25],color="black")
    ax.plot([0,16.5],[65,65],color="black")
    ax.plot([16.5,0],[25,25],color="black")

    #Right Penalty Area
    ax.plot([130,113.5],[65,65],color="black")
    ax.plot([113.5,113.5],[65,25],color="black")
    ax.plot([113.5,130],[25,25],color="black")

    #Left 6-yard Box
    ax.plot([0,5.5],[54,54],color="black")
    ax.plot([5.5,5.5],[54,36],color="black")
    ax.plot([5.5,0.5],[36,36],color="black")

    #Right 6-yard Box
    ax.plot([130,124.5],[54,54],color="black")
    ax.plot([124.5,124.5],[54,36],color="black")
    ax.plot([124.5,130],[36,36],color="black")

    #Prepare Circles
    centreCircle = plt.Circle((65,45),9.15,color="black",fill=False)
    centreSpot = plt.Circle((65,45),0.8,color="black")
    leftPenSpot = plt.Circle((11,45),0.8,color="black")
    rightPenSpot = plt.Circle((119,45),0.8,color="black")

    #Draw Circles
    ax.add_patch(centreCircle)
    ax.add_patch(centreSpot)
    ax.add_patch(leftPenSpot)
    ax.add_patch(rightPenSpot)

    #Prepare Arcs
    leftArc = Arc((11,45),height=18.3,width=18.3,angle=0,theta1=310,theta2=50,color="black")
    rightArc = Arc((119,45),height=18.3,width=18.3,angle=0,theta1=130,theta2=230,color="black")

    #Draw Arcs
    ax.add_patch(leftArc)
    ax.add_patch(rightArc)

    #Tidy Axes
    plt.axis('off')
    
    return ax


def plot_goalmouth(ax):
    ax.plot([0,0], [0,8], color='black', linewidth=5) # left post
    ax.plot([0,24], [8,8], color='black', linewidth=5) # crossbar
    ax.plot([24,24], [8,0], color='black', linewidth=5) # right post
    
    ax.set_aspect('equal')
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    return ax