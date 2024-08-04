from gui import UIContainer, CreateUIElement
import tkinter
from tkinter import filedialog
from pygame.image import load
from pygame.math import Vector2
import pygame.transform
import random
import math
import os
import pickle
import json

# ~~~ EVENT FUNCTIONS ~~~

# An event which will change the active screen on the main window
def ChangeMainWindowSection(sharedMemory,root,buttonId):
    #Map each button to its corrsponding section
    panelIds = {
        "#Nav_Properties" : "#Properties",
        "#Nav_File" : "#File_Options",
        "#Nav_Run" : "#SPProperties",
        "#Nav_Help" : "#Help"
    }
    #Hide all panels in the main window except for the one which has just been selected
    for key in panelIds:
        panel = GetElement(root,f"#Main_Window.{panelIds[key]}")
        panel.hide()
    if buttonId == "#Nav_Properties" and not sharedMemory["Edit"]:
        return
    panel = GetElement(root,f"#Main_Window.{panelIds[buttonId]}")
    panel.show()
    if buttonId == "#Nav_Properties":
        UpdatePropertiesUI(sharedMemory)
        
# An event which will update the text connected to a slider when it is moved
def UpdateSliderText(element,value):
    # Get the textbox associated with the slider and update its text
    textValue = GetElement(element.ui_container,element.object_ids[-1]+"_Box")
    textValue.set_text(str(value))
    return value

# This event updates a slider's position when its text value is changed
def UpdateSlider(element,text):
    slider = GetElement(element.ui_container,element.object_ids[-1][:-4])
    # Validate the new slider value
    try:
        value = InBounds(int(text),slider.value_range)
    except ValueError:
        value = slider.get_current_value()
    #Set the slider and text value to the validated value
    slider.set_current_value(value) 
    element.set_text(str(value))
    return value        

# Function which will change the help section to show the most recent page
def UpdateHelpSection(root,sharedMemory):
    # Load the help info json file
    helpInfo = json.load(open("help.json","r"))
    # Make sure the page number is within valid limits
    sharedMemory["HelpPage"] = InBounds(sharedMemory["HelpPage"],(1,len(helpInfo["explanation"])))
    page = sharedMemory["HelpPage"]
    image = load(helpInfo["image"][str(page)])
    text = helpInfo["explanation"][str(page)]
    helpSection = GetElement(root,"#Main_Window.#Help")
    # Update text, page and image of the help section
    imgUI = GetElement(helpSection,"#Help_Image")
    # Ensure the image is of constant size
    image = pygame.transform.smoothscale(image,(imgUI.rect.width,imgUI.rect.height))
    imgUI.set_image(image)
    GetElement(helpSection,"#Help_Text").set_text(text)
    GetElement(helpSection,"#Help_Page").set_text(f"Page # {page}/{len(helpInfo['explanation'])}")
    
# This function will update properties displayed in the UI
def UpdatePropertiesUI(sharedMemory):
    #Get the selected object
    object = sharedMemory["Selected"]
    # Get properties info
    properties = GetElement(sharedMemory["MainUIManager"].get_root_container(),"#Main_Window.#Properties")
    if not properties.visible:
        # If the properties window is hidden, there is no need to update UI
        return
    eProp = GetElement(properties,"#Edge_Properties")
    nProp = GetElement(properties,"#Node_Properties")
    # Initially both panels should be turned off
    eProp.hide()
    nProp.hide()
    if object == None:
        # If no object is selected, no properties should be shown
        return
    if object.type == "Node":
        # Update and display node properties UI
        GetElement(nProp,"#Node_Name_Input").set_text(object.name)
        GetElement(nProp,"#Node_Colour_Input").set_text(object.colour[1::])

        nProp.show()
    elif object.type == "Edge":
        # Update and display edge properties UI
        GetElement(eProp,"#Edge_Name_Input").set_text(object.name)
        GetElement(eProp,"#Edge_Colour_Input").set_text(object.colour[1::])
        # Update the sliders and their textbox values
        UpdateSlider(GetElement(eProp,"#Edge_Weight_Input_Box"),object.weight)
        UpdateSliderText(GetElement(eProp,"#Edge_Weight_Input"),object.weight)
        UpdateSlider(GetElement(eProp,"#Edge_Length_Input_Box"),object.length)
        UpdateSliderText(GetElement(eProp,"#Edge_Length_Input"),object.length)
        eProp.show()

# Updates the UI and graph for the algorithm visualisation of SPA
def ApplyStep(sharedMemory,root,stepChange=0):
    # If the user tries to go out of the bounds of number of steps
    # No change should be made to the graph
    steps = sharedMemory["Steps"]
    if (sharedMemory["Step"] == 0 and stepChange == -1) or (sharedMemory["Step"] == len(steps)-1 and stepChange == 1):
        return
    window = GetElement(root,"#Explantion_Window")
    lastStep = steps[sharedMemory["Step"]]
    sharedMemory["Step"] += stepChange
    stepN = sharedMemory["Step"]
    step = sharedMemory["Steps"][stepN]
    # Update the step counter
    GetElement(window,"#Step_Number").set_text(f"Step {stepN+1} of {len(steps)}")
    # Update the text
    GetElement(window,"#Algorithm_Text").set_text(steps[stepN].explanation)

    # If the step has changed, apply the backward operations for the last step's temporary operations
    if stepChange != 0:
        for temp in lastStep.tempOps:
            temp.Backward(sharedMemory)

    # If the user goes backward in the set of steps,
    # the permanent operations should be undone for the previous step
    if stepChange == -1:
        for perm in lastStep.permOps:
            perm.Backward(sharedMemory)

    # Apply the permanent operations of the current step when incrementing
    else:
        for perm in step.permOps:
            perm.Forward(sharedMemory)

    # Apply the temporary operations for the current step
    for temp in step.tempOps:
        temp.Forward(sharedMemory)

# Complete all steps to the graph
def SkipSteps(sharedMemory,root):
    steps = sharedMemory["Steps"]

    # Undo the temporary operation of the current step
    for temp in steps[sharedMemory["Step"]].tempOps:
        temp.Backward(sharedMemory)

    while sharedMemory["Step"] < len(steps) - 1:
        # Apply the permanent operations for every subsequent step
        sharedMemory["Step"] += 1
        for perm in steps[sharedMemory["Step"]].permOps:
            perm.Forward(sharedMemory)
    
    window = GetElement(root,"#Explantion_Window")
    # Update the step counter
    GetElement(window,"#Step_Number").set_text(f"Step {sharedMemory['Step']+1} of {len(steps)}")
    # Update the text
    GetElement(window,"#Algorithm_Text").set_text(steps[sharedMemory['Step']].explanation)

    # Apply the temporary operations for the final step
    for temp in steps[sharedMemory["Step"]].tempOps:
        temp.Forward(sharedMemory)

# Return back to the first step
def RestartSteps(sharedMemory,root,full = False):
    steps = sharedMemory["Steps"]

    # Undo the temporary operation of the current step
    for temp in steps[sharedMemory["Step"]].tempOps:
        temp.Backward(sharedMemory)

    # If the full boolean is true, the first step is also undone (cleanup)
    while sharedMemory["Step"]+full > 0:
        # Undo the permanent operations for every previous step
        for perm in steps[sharedMemory["Step"]].permOps:
            perm.Backward(sharedMemory)
        sharedMemory["Step"] -= 1
    
    window = GetElement(root,"#Explantion_Window")
    # Update the step counter
    GetElement(window,"#Step_Number").set_text(f"Step {sharedMemory['Step']+1} of {len(steps)}")
    # Update the text
    GetElement(window,"#Algorithm_Text").set_text(steps[sharedMemory['Step']].explanation)

    # Apply the temporary operations for the first step
    for temp in steps[sharedMemory["Step"]].tempOps:
        temp.Forward(sharedMemory)

# An event for adjusting environment scale when a button is pressed
def ZoomButton(sharedMemory,objectId,scaleSpeed,scaleBounds):
    scale = sharedMemory["Scale"]
    # The zoom in button increases the scale by an aribitrary number of units and vice versa
    scale += scaleSpeed * 5 * [-1,1][objectId == "#Zoom_In"]
    scale = InBounds(scale,scaleBounds)
    sharedMemory["Scale"] = scale

# An event for adjusting scale when the mouse wheel is moved
def ZoomWheel(event,sharedMemory,scaleSpeed,scaleBounds):
    # Moving the mouse wheel will change the scale of the environment
    scale = sharedMemory["Scale"] + scaleSpeed * event.y
    #Ensure the scale is within certain bounds
    scale = InBounds(scale,scaleBounds)
    sharedMemory["Scale"] = scale

# A function which checks if the camera position needs to be updated
def MoveCamera(root,timedelta,mouseStates,sharedMemory):
    # If the middle mouse button is pressed, or left mouse button is pressed with either the move camera or select tool
    # The camera won't move if the user was pressing/dragging a button
    if not CheckHover(root,timedelta) and ((mouseStates[0] and sharedMemory["SelectedTool"] in ["#Move_Camera","#Select"] and not sharedMemory["Drag"]) or mouseStates[1]):
        movement = sharedMemory["MouseMovement"] / sharedMemory["Scale"]
        movement.x *= -1
        sharedMemory["CameraPosition"] += movement
        return True
    return False

# ~~~ MAIN FUNCTIONS ~~~

# Function used to reference different UI elements from a parent element. For example, finding a button within the main window
# Object Id path should be formatted as : "childId.childOfChildId" etc.
def GetElement(container,objectIdPath):
    #Allow the container parameter to accept container and element objects
    if type(container) != UIContainer:
        try:
            #The panel_container associated with the element is retrieved
            container = container.panel_container
        except AttributeError:
            raise ValueError("Container must of type UIContainer or subclass of UIElement")
    #Split the path into each container and the final element to be found
    containers = objectIdPath.split(".")
    #Iterate over each Id to be found in the objectIdPath
    for i in range(len(containers)):
        ID = containers[i]
        matchingElements = []
        #Check which elements have the searched ID
        for element in container.elements:
            if element.object_ids[-1] == ID:
                matchingElements.append(element)
        #Ensure exactly one result was found. If not raise an appropriate error
        if len(matchingElements) == 0:
            raise Exception(f"Could not find find element with object ID: {ID} ")
        elif len(matchingElements) == 1:
            #Set the new container to the found element
            if i == len(containers) - 1:
                return matchingElements[0]
            container = matchingElements[0].panel_container
        else:
            raise Exception(f"Object Ids must be unique. Multiple elements had object ID: {ID}")

#Checks if any UI elements are being hovered over
def CheckHover(root,td):
    for element in root.elements:
        #If a given visible element is being hovered over, return True
        if element.visible and element.check_hover(td,False):
            return True
    return False

# Function to convert a screen position to a corresponding position in the environment 
def ScnToEnv(screenPos, sharedMemory):
    if type(screenPos) in [tuple,list]:
        screenPos = Vector2(*screenPos)

    # Get variables from shared memory about the environment
    scale = sharedMemory["Scale"]
    cameraPosition = sharedMemory["CameraPosition"]
    screenSize = sharedMemory["ScreenSize"]
    
    # Centre the envPos to the screen centre
    envPos = screenPos - (screenSize / 2) 
    # Scale the position
    envPos /= scale
    # Invert the Y-position and add on the camera position
    # This gets a global position in the environment
    envPos.y *= -1
    envPos += cameraPosition
    
    return envPos

#Function to convert a position in the environment to a coordinate on the screen
def EnvToScn(envPos,sharedMemory):
    if type(envPos) in [tuple,list]:
        envPos = Vector2(*envPos)

    # Get variables from shared memory about the environment
    scale = sharedMemory["Scale"]
    cameraPosition = sharedMemory["CameraPosition"]
    screenSize = sharedMemory["ScreenSize"]
    
    # Get the relative distance to the camera position and invert the Y-position
    screenPos = envPos - cameraPosition
    screenPos.y *= -1
    # Reverse the applied scale to the position
    screenPos *= scale
    # Set (0,0) to the top left of the screen
    screenPos += screenSize / 2
    
    return screenPos

def UpdateSPProperties(root,sharedMemory):
    spp = GetElement(root,"#Main_Window.#SPProperties")
    if spp.visible:
        # Check if the start and end nodes have changed
        startNode = NodeFromID(sharedMemory["SPAStartNode"],sharedMemory)
        if startNode == None:
            # Reset the input if the node no longer exists
            GetElement(spp,"#Start_Node_Input").set_text("Select A Node")
            sharedMemory["SPAStartNode"] = None
        else:
            GetElement(spp,"#Start_Node_Input").set_text(startNode.name)
        endNode = NodeFromID(sharedMemory["SPAEndNode"],sharedMemory)
        if endNode == None:
            # Reset the input if the node no longer exists
            GetElement(spp,"#End_Node_Input").set_text("Select A Node")
            sharedMemory["SPAEndNode"] = None
        else:
            GetElement(spp,"#End_Node_Input").set_text(endNode.name)

# Creates the grid for the environment
# The gridLineSpacing parameter determines how far apart grid lines are generated
def CreateGrid(screen,gridLineSpacing,sharedMemory):
    #Get bounds set to opposite corners of the screen
    screenSize = screen.get_size()
    topLeftBound = ScnToEnv((0,0),sharedMemory)
    bottomRightBound = ScnToEnv(screenSize,sharedMemory)

    #An array of all grid lines parallel to the y-axis
    xGrid = []
    #Each grid line should be spaced appropriately and one line should pass through (0,0) in environment space
    startX = int(topLeftBound.x // gridLineSpacing)+1
    endX = int(bottomRightBound.x // gridLineSpacing)+1

    for x in range(startX,endX):
        startPoint = EnvToScn((x * gridLineSpacing,topLeftBound.y),sharedMemory)
        endPoint = EnvToScn((x * gridLineSpacing,bottomRightBound.y),sharedMemory)
        xGrid.append((startPoint,endPoint,[1,2][x == 0]))

    #Repeat for the grid lines parallel to the x-axis
    yGrid = []
    startY = int(bottomRightBound.y // gridLineSpacing)+1
    endY = int(topLeftBound.y // gridLineSpacing)+1
    for y in range(startY,endY):
        startPoint = EnvToScn((topLeftBound.x,y * gridLineSpacing),sharedMemory)
        endPoint = EnvToScn((bottomRightBound.x,y * gridLineSpacing ),sharedMemory)
        yGrid.append((startPoint,endPoint,[1,2][y == 0]))
        
    #Return the created grid
    return xGrid+yGrid

def NewEnv(sharedMemory):
    # Destroy all nodes/edges
    while sharedMemory["Nodes"] != []:
        sharedMemory["Nodes"][0].Destroy(sharedMemory)
    # Reset Camera
    sharedMemory["CameraPosition"] = Vector2(0,0)
    sharedMemory["Scale"] = sharedMemory["ScaleBounds"][0]
    # Reset tool variables
    sharedMemory["SelectedTool"] = "#Move_Camera"
    sharedMemory["UndoStack"] = []
    sharedMemory["RedoStack"] = []
    sharedMemory["Changed"] = False
    sharedMemory["NodeCount"] = 1
    sharedMemory["EdgeCount"] = 1
    sharedMemory["SaveDir"] = None

#Ensures a value is within a set of bounds
def InBounds(value,bounds):
    # Value is less than lower bound
    if value < bounds[0]:
        return bounds[0]
    # Value is greater than upper bound
    elif value > bounds[1]:
        return bounds[1]
    return value

# ~~~ Environment Functions ~~~

# A function which will readujst all nodes in the environment
# The maxforce and slope parameters are arbitrary constants
# These determine the velocity and maximum values of the adjustment forces
def NodeReadjustment(sharedMemory,timedelta):
    maxForce = sharedMemory["MaxForce"]
    slope = sharedMemory["AdjustmentRate"]
    optimalDistance = sharedMemory["OptimalNodeDistance"]
    nodes = sharedMemory["Nodes"]
    edges = sharedMemory["Edges"]
    lengthRatio = sharedMemory["LengthToUnitRatio"]

    for node1 in nodes:
        if node1.selected and sharedMemory["Drag"]:
            continue
        for node2 in nodes:
            if node1 == node2: # Ensure the nodes are unique
                continue

            # Calculate the distance between nodes
            distance = (node2.position - node1.position).magnitude()
            if distance < 0.1: # if nodes are too close together, a random direction is applied
                dir = random.randint(-180,180) / 180
                direction = Vector2(math.cos(dir * math.pi),math.sin(dir * math.pi))
            else: 
                direction = (node2.position - node1.position) / distance
            
            #If nodes are connected, an attractive force is applied
            if node2 in node1.connectedNodes:
                edge = node1.GetEdgeTo(node2)
                force = 5 * maxForce * math.tanh(((distance-edge.length*lengthRatio)**3) / (slope**3))
                node1.velocity += force * direction
            #Nodes not connected by the other node will have a repulsive force applied if they are closer than optimal
            elif distance < optimalDistance:
                force = -maxForce * math.cos((math.pi * distance / (2*optimalDistance)))
                node1.velocity += force * direction
    
    # Adjust node positions using their new velocities
    for node in nodes:
        #Time delta ensures the distance travelled is constant per second
        node.position += node.velocity * timedelta
        node.velocity = Vector2(0,0) # Reset the velocity
        # Adjust the position of the node's labels
        size = Vector2(node.UILabel.rect.size)
        #The centre of the label should be updated to the centre of the node
        position = EnvToScn(node.position,sharedMemory) - size / 2
        node.UILabel.rect.x = position.x
        node.UILabel.rect.y = position.y
        text = GetElement(node.UILabel,"#Label_Text")
        text.rect.x = position.x
        text.rect.y = position.y

    # Adjust the position of the weight labels
    for edge in edges:
        size = Vector2(edge.UILabel.rect.size)
        #The centre of the label should be updated to the edge's midpoint
        position = EnvToScn(edge.Mid(),sharedMemory) - size / 2
        edge.UILabel.rect.x = position.x
        edge.UILabel.rect.y = position.y
        text = GetElement(edge.UILabel,"#Label_Text")
        text.rect.x = position.x
        text.rect.y = position.y

# This function will determine if there is an edge or node at the position at which the cursor was pressed
def Select(sharedMemory,position):
    #Convert the screen position to an environment position
    position = ScnToEnv(position,sharedMemory)
    # Check if a node was selected
    for node in sharedMemory["Nodes"]:
        distance = (position - node.position).magnitude()
        #If the distance is less than the radius of the node, the user clicked on the node
        # An arbitrary value is added to make it easier to select nodes
        if distance <= node.radius + 20:
            return node

    # Check if an edge was selected
    for edge in sharedMemory["Edges"]:
        # Get the normalised direction from one edge node to the other
        try:
            normal = (edge.nodeB.position - edge.nodeA.position).normalize()
        except:
            continue
        # Set local origin to the centre of the edge
        lPos = position - edge.Mid()
        # Apply a rotation matrix to the position so its x-axis is parallel to the edge.
        # The y-axis will be parallel with the edge's normal
        lPos = Vector2(lPos.x * normal.x + lPos.y * normal.y, lPos.y * normal.x - lPos.x * normal.y)
        # If the local position is within the rectangular bounds of the edge, the edge has been selected
        # Calculate the length of the edge
        length = (edge.nodeA.position - edge.nodeB.position).magnitude()
        # An aribirary value is added to the width bounds to make selection of edges easier.
        if (lPos.x < length /2 and lPos.x > -length / 2) and (lPos.y < edge.width /2 + 20 and lPos.y > -edge.width / 2 - 20) :
            return edge

#This function represents the process for undoing an action to the graph
def Undo(sharedMemory):
    #Check that there is an operation to apply
    if sharedMemory["UndoStack"] == []:
        return
    # Get the operation from the top of the undo stack and move it to the redo stack
    operation = sharedMemory["UndoStack"].pop()
    sharedMemory["RedoStack"].append(operation)
    # Apply the backward action
    operation.Backward(sharedMemory)

#This function represents the process for redoing an undone action to the graph
def Redo(sharedMemory):
    #Check that there is an operation to apply
    if sharedMemory["RedoStack"] == []:
        return
    # Get the operation from the top of the redo stack and move it to the undo stack
    operation = sharedMemory["RedoStack"].pop()
    sharedMemory["UndoStack"].append(operation)
    # Apply the backward action
    operation.Forward(sharedMemory)

# The following two functions will be used to locate an existing node based on a unique ID
# This will be important for operations where object references cannot be relied upon

def NodeFromID(id,sharedMemory):
    for node in sharedMemory["Nodes"]:
        if node.id == id:
            return node
    return None

def EdgeFromID(id,sharedMemory):
    for edge in sharedMemory["Edges"]:
        if edge.id == id:
            return edge
    return None

# This function will update data about whichever object should be selected
# It also ensures that the previously selected object is handled apporpriately
def UpdateSelection(sharedMemory,object):
    if sharedMemory["Selected"] != None:
        # Deselect the previous object
        sharedMemory["Selected"].selected = False
    sharedMemory["Selected"] = object # Updates the variable for sharedMemory
    if object != None:
        # Set the selected parameter in the object to true
        object.selected = True

    UpdatePropertiesUI(sharedMemory)
    