# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 19:49:54 2020

This GUI is designed to assess the just noticeable differences between the 
length of a pair of lines. The aim is to measure the threshold in pixels at 
which an observer is able to perceive a line longer than the other when the given
lines have a specific width and are separated a certain distance from each other.

An adaptive method based on the posterior distribution is utilized, making 
data collection more efficient. The core method known as the Psi method 
according to [1] has been modified to avoid the same stimulus being presented 
in multiple consecutive trials throughout the test, thus gaining more confidence
on the threshold value and slope of the psychometric function. 

The stimuli are presented to the observer as a two-alternative forced-choice (2AFC).
This is, the lines are presented at the same time, next to each other and the 
observer needs to decide which line seems the longest.

The Psi method estimates the sensory threshold based on previous responses. 
A psychometric function is fitted to the data collected so far so that the 
logarithmic likelihood is maximized. This is implemented by searching for the
minimum negative logarithmic likelihood using the function 'minimize' from 
scipy.optimize and the 'Nelder-Mead' method (see the script MaxLikelihoodEstimation.py 
for further information)

A modification to the method described in [1] is implemented to avoid the same 
stimulus intensity to be presented multiple consecutive times. This tends to 
happen with a small discrete number of possible stimulus intensities. 
The modification consist of presenting a value of the stimulus intensity within a
range around the suggested value by the adaptive method and not necessarily 
the exact closest value to the threshold estimate. This allows gaining more resolution 
around the true threshold and prevents the adaptive method from getting ‘stuck’ 
in the same value.

The effect of this modification and the method's performance can be tested using the
script AdaptiveTest_UserSimulation.py. The test parameters can be manipulated to 
see the effect in order to design a suitable experiment depending on the application.

At the end of the experiment, the test subject can view his/her results and 
fitted psychometric function


[1] Psychophysics. A practical introduction. F. A. A. Kingdom & N. Prins

@author: Marina Torrente Rodriguez

TO DOs:
    
    - Add goodness of fit metric
    - Add counter
    - Save test results
    - Show test progress figure
    - Add signal detection theory test processing and metrics (ROC curves)
    - Add figure name to results figure

    
"""


# Required libraries
import tkinter as tk
import random
import numpy as np
from MaxLikelihoodEstimation import MLE_search
from PsychometricFunctionClass import PsychometricFunction
import time

# Threshold measurements varaibles
# Test parameters
MaxTrials = 30                  # After which the test stops
MinTrials = 0.30*MaxTrials      # Stimuli intensity for the first number of trials is presented at random
StimLevels = np.arange(0,15,1)  # Array of stimulus intensity levels
Gamma = 0.5                     # Depends on the type of test; the M-Force Choice methods Gamma = 1/M
Lambda = 0.01                   # If not known from experience, this is usually set to 0.01 
typef = "Logistic"              # Maximum number of time the same value of stimulus intensity can be presented consecutively


def NewLinesLengths(size_base, size_add):

    # Baseline length of both lines equals to 'size_base'
    size_lineA = size_base
    size_lineB = size_base
    
    # Additional length summed to the baseline lenth to 
    # either lina A or B randomly
    if random.choice(['A','B']) == 'A':
        size_lineA += size_add
    else:
        size_lineB += size_add
        
    return size_lineA, size_lineB

def LinesCoordinates(size_line):
    # Generate vertical and horizontal coordinates in the midle of the canvas
    # base on the length of the line
    y1 = (canvas_height-size_line)/2
    y2 = y1 + size_line
    coord = (canvas_width/2, y1, canvas_width/2, y2)
    return coord


def InitialiseLines(size_base):
    
    # Random choice of stimuli levels is assigned as the additional length of one 
    # of the presented lines
    size_lineA, size_lineB = NewLinesLengths(size_base, np.random.choice(StimLevels))
    
    # Save lines length values in array
    lineA_length.append(size_lineA)
    lineB_length.append(size_lineB)
    
    # Draw lines on Canvas A and B
    lineA = canvasA.create_line(LinesCoordinates(size_lineA))
    lineB = canvasB.create_line(LinesCoordinates(size_lineB))
    
    return lineA, lineB


def HideLines():

    # Give lines length '0'
    canvasA.coords(lineA, LinesCoordinates(0)) 
    canvasB.coords(lineB, LinesCoordinates(0))

    # Add delay for lines to hide before new lines are presented
    root.update()
    time.sleep(0.2)


def GetNextLengths():
    
    # Choose next stimulus intensity randomly for the first few trials
    if root.counter < MinTrials: 
        # Choose next stimulus intensity randomly
        StimIndex = random.choice(range(len(StimLevels)))
        
        
    else:            
        # Present values by Psi method: 
        # fitting PF taking the estimate PF as the posterior probablity
        results = MLE_search(Gamma, Lambda, typef, StimLevels, NumCorrect, Total)
        
        # Use entropy's maximum likelihood value if the search terminates 
        # succesfully otherwise choose next stimulus intensity at random
        if results.success is True:
            # Print PF parameters found
            alpha, beta = results.x[0], results.x[1]
            print("alpha = ", alpha, " ; beta = ", beta)
            
            # Find stim level closest to alpha and set as current 
            diff = abs(StimLevels-results.x[0])
            StimIndex = np.unravel_index(np.argmin(diff, axis=0), diff.shape)
            StimIndex = np.random.choice(a=np.arange(StimIndex[0]-2,StimIndex[0]+3,1))
            if StimIndex < 0:
                StimIndex = 0
            elif StimIndex > len(StimLevels)-1:
                StimIndex = len(StimLevels)-1

        else:
            # Choose next stimulus intensity at random
            StimIndex = random.choice(range(len(StimLevels)))

    # Current Stimulus level by obtained index
    size_add = StimLevels[StimIndex]

    return NewLinesLengths(size_base, size_add)

   
def PresentNextLines():

    # Get next lines lengths values according to adaptive method
    size_lineA, size_lineB = GetNextLengths()

    # Store new lengths values                
    lineA_length.append(size_lineA)
    lineB_length.append(size_lineB)
    
    # Update lines A and B lengths
    canvasA.coords(lineA, LinesCoordinates(size_lineA)) 
    canvasB.coords(lineB, LinesCoordinates(size_lineB)) 
    
    # Deselect A/B radiobuttons#
    selectA.deselect()
    selectB.deselect()


def UpdateResultsVariablesByChoice():
    
    # Find index of stimulus
    stimulus_value = abs(lineA_length[-1]-lineB_length[-1])
    stimulus_index = np.where(StimLevels == stimulus_value)
    
    # Increment the total number of stimulus intensity presented
    Total[stimulus_index] += 1
    print(stimulus_value)
    
    # Determine correct or incorrect response
    if lineA_length[-1] > lineB_length[-1]:
        correct = 'A'
    elif lineB_length[-1] > lineA_length[-1]:
        correct = 'B'
    else:
        correct = 'Equal'
            
    # Increment number of correct responses if required
    if correct == choice[-1]:
        NumCorrect[stimulus_index] += 1
    elif correct == 'Equal':
        NumCorrect[stimulus_index] += 0.5        


def HideWidgets():
    canvasA.grid_forget()
    canvasB.grid_forget()
    selectA.grid_forget()
    selectB.grid_forget()
    btn_next.grid_forget()


def PlotResults():

    # Find PF parameters: alpha and beta
    results = MLE_search(Gamma, Lambda, typef, StimLevels, NumCorrect, Total)

    # Define PF
    PF = PsychometricFunction(Alpha=results.x[0], Beta=results.x[1],
                              Gamma=Gamma, Lambda=Lambda, type_func=typef)

    # x-axis vector            
    x = np.linspace(np.min(StimLevels),np.max(StimLevels),100)

    # Plot PF and measured points
    PF.plot_PFestimate(x, StimLevels, NumCorrect, Total)


# Define Next button callback function
def NextCallback():
    
    # Increase trail counter
    root.counter += 1
    
    # Check if an option is selected, otherwise show error message
    if not Option.get():
        print("No choice made!")

    else:

        # Hide lines before presenting new lengths to aviodvisual 
        # changes to provide a cue based on a change happening rather 
        # than a difference in length perceived 
        HideLines()
        
        # Store results
        choice.append(Option.get())
        
        # Update reults variable
        UpdateResultsVariablesByChoice()
        
        # Print data
        print("Trail counter: ", root.counter)
        print("Line A:",lineA_length)
        print("Line B:",lineB_length)
        print("Choice: ", choice)

        # If number of trails has not exceed a maximum, 
        # then Show next pair of lines
        if root.counter < MaxTrials:
            
            PresentNextLines()
                                    
        # Otherwise, end program and show results        
        else:
            
            # Hide widgets
            HideWidgets()
            
            # Show end message
            print("END!")
            intrs_txt.config(text="You have finished the test!")
            
            # Plot results
            PlotResults()
            
            
# Initial varaibles
root = tk.Tk()
root.counter = 0
choice = []
stim = []
lineA_length = []
lineB_length = []
NumCorrect = np.zeros(len(StimLevels))
Total = np.zeros(len(StimLevels))


# Intructions text widget
intrs_txt = tk.Label(root, text="Select the longest line:",font=("Helvetica", 20))    

# Canvas widgets' size to draw linesLines in
canvas_width = 200
canvas_height = 500
canvasA = tk.Canvas(root, width=canvas_width, height=canvas_height)
canvasB = tk.Canvas(root, width=canvas_width, height=canvas_height)

# Initial lines length based on random choice of stimulus intentity
size_base = 150 # baseline lines' length
lineA, lineB = InitialiseLines(size_base)

# Select buttons
Option = tk.StringVar()
selectA = tk.Radiobutton(root, text="A", variable= Option, value="A",
                         tristatevalue=0,
                         font=("Helvetica",15), width=5, pady = 20)
selectB = tk.Radiobutton(root, text="B", variable= Option, value="B",
                         tristatevalue=0,
                         font=("Helvetica",15), width=5, pady = 20)
            
# Next button
btn_next = tk.Button(root,text="Next",font=("Helvetica", 16),
                     command=lambda *args: NextCallback())

    
# Place widgets
intrs_txt.grid(columnspan=5)
canvasA.grid(row=1,column=0)
canvasB.grid(row=1,column=2)
selectA.grid(row=2, column=0)
selectB.grid(row=2, column=2)
btn_next.grid(row=3,column=1)

# Initialise GUI
root.geometry("600x800")
root.mainloop()


