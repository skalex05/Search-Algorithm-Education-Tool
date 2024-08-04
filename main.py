from gui import * # Imports the GenerateUI function aswell as pygame and pygame_gui
from functions import *
from classes import *
import time
import json

# Quits the pygame instance
def Quit(sharedMemory):
    sharedMemory["Run"] = False
    pygame.quit()

# Create a mainloop where the UI will be updated and user input will be processed
if __name__ == "__main__":
    # PROGRAM VARIABLES

    framerate = 60 # Set the maximum number of times the UI and environment will be updated per second
    gridLineSpacing = 100 # How far apart grid lines are generated
    scaleSpeed = 0.05 # The rate at which scale can change
    scaleBounds = (0.3,1.6)

    gridColour = (56,61,61)
    bgColour = (210,210,210) # Set the rgb background colour of the environment
    sharedMemory = { # Initialise a dictionary for data which will be shared across different areas of the program
        "Run" : True, # This boolean will determine when all threads should close
        "CameraPosition" : Vector2(0,0), # Represents the user's position in the environment
        "ScaleBounds" : (0.3,1.6), # The scale of the environment must be contained to these bounds
        "Scale" : scaleBounds[0], # The scale in the environment view
        "ScreenSize" : Vector2(pygame.display.get_desktop_sizes()[0])-Vector2(0,80), # The size of the screen
        "MousePosition" : Vector2(0,0), # Contains where the mouse currently is on screen
        "MouseMovement" : Vector2(0,0), # Contains the relative movement of the mouse
        "SelectedTool" : "#Select", # The tool that should be used when the left click button is pressed
        "Selected" : None,  # Represents the currently selected object
        "SaveDir": None, # The default location used to save files
        "Changed": False, # The graph has not been saved in this state
        "Drag": False, # Denotes if the selected object should be dragged
        "UndoStack": [], # A collection of operations that can be undone
        "RedoStack": [], # A collection of operations that can be redone
        "Nodes" : [],   # Contains all nodes in the environment
        "Edges" : [],    # Contains all edges in the environment
        "LengthToUnitRatio" : 25, # One unit of length in an edge represents 50 units in the environment
        "MaxForce" : 500, # Maximum force which can be applied to nodes
        "AdjustmentRate" : 200, # The rate at which nodes connected by an edge move to reach their desired length
        "OptimalNodeDistance" : 500, # Distance disconnected nodes want to be from eachother
        "EdgeCount" : 1, # Counts the number of edges
        "NodeCount" : 1, # Counts the number of edges
        "HeuristicMultiplier" : 0.008, # A scale applied to the distance between nodes to calculate heuristic costs
        "HelpPage": 1, # Page number of the help section
        "SPAStartNode" : None, # Stores the start node where a SPA will be performed
        "SPAEndNode" : None, # Stores the end node where a SPA will be performed
        "SPA" : None, # Stores the SPA that is being performed
        "SelectedSPA" : None, # The SPA the user has selected to be performed
        "Steps" : [], # When an SPA is run on a graph, a set of steps are created to show how to calculate the shortest route
        "Step" : 0, # The index of the currently displayed step
        "Edit" : True # Boolean which determines if the user can edit their graph
        }

    # Generate the UI from gui.py and retrieve the pygame surface and GUI manager
    screen, mainUIManager, envUIManager = GenerateUI(sharedMemory["ScreenSize"])

    sharedMemory["MainUIManager"] = mainUIManager
    sharedMemory["EnvUIManager"] = envUIManager

    root = mainUIManager.get_root_container()

    clock = pygame.time.Clock() # Object which will be responsible for managing the framerate/frametime of the UI

    # Create Environment Grid
    grid = CreateGrid(screen,gridLineSpacing,sharedMemory)
    
    FPS = GetElement(root,"#FPS")
    
    edgeStart = None    # A variable used to represent the starting node of an edge to be created

    selectedSlider = None

    while sharedMemory["Run"]:        
        timedelta = clock.tick(framerate) / 1000 # Limit the framerate and retrieve the time in miliseconds since the last frame
        if timedelta != 0:
            GetElement(FPS,"#Label_Text").set_text(f"FPS: {int(1/timedelta)}")
        # NEW FRAME
        # Update all UI elements
        
        mainUIManager.update(timedelta)
        envUIManager.update(timedelta)

        # Clear the screen
        screen.fill(bgColour)
        # Render the grid
        for gridLine in grid:
            pygame.draw.line(screen,gridColour,*gridLine)
        
        # Render edges
        for edge in sharedMemory["Edges"]:
            edge.Draw(screen,sharedMemory)

        # Draw a line to the user's cursor from the node they have selected
        # This will help the user visualise creating edges
        if edgeStart != None:
            pygame.draw.line(screen,"#5e6060",EnvToScn(edgeStart.position,sharedMemory),sharedMemory["MousePosition"],width = int(25 * sharedMemory["Scale"]))

        # Render nodes
        for node in sharedMemory["Nodes"]:
            node.Draw(screen,sharedMemory)

        # Repaint the UI
        envUIManager.draw_ui(screen)
        mainUIManager.draw_ui(screen)

        pygame.display.update()

        # Update the position of the mouse and how much it has moved since the last frame
        sharedMemory["MousePosition"] = Vector2(pygame.mouse.get_pos())
        sharedMemory["MouseMovement"] = Vector2(pygame.mouse.get_rel())
        #Get which mouse buttons are currently held down
        mouseStates = pygame.mouse.get_pressed()
        
        changePersp = False

        # EVENT / INPUT PROCESSING
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # If the most recent version of the program has not been saved, prompt them to save it first
                if sharedMemory["Changed"]:
                    Prompt(sharedMemory,mainUIManager,"Quit Without Saving","Are you sure you want to quit without saving?","#Save_Quit_Prompt",actionButton="Yes")
                else:
                    Quit(sharedMemory)
            if event.type == pygame.VIDEORESIZE:
                # Update the size of the screen and all variables storing the screen size
                size = (event.w,event.h)
                envUIManager.set_window_resolution(size)
                mainUIManager.set_window_resolution(size)
                sharedMemory["ScreenSize"] = Vector2(size)
                changePersp = True
            elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                #Update the chosen SPA
                sharedMemory["SelectedSPA"] = event.text
            elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                #Process a dialogue confirmation depending on its id
                objectId = event.ui_element.object_ids[-1]
                if objectId == "#Save_Quit_Prompt":
                    # Quit the program by setting run to false and quitting pygame
                    Quit(sharedMemory)
                elif objectId == "#Save_New_Prompt":
                    # Create a new environment
                    NewEnv(sharedMemory)
                    changePersp = True
                elif objectId == "#Save_Open_Prompt":
                    # Open a new file
                    Open(sharedMemory)
                    changePersp = True
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                # Get the most specific objectId about an element
                objectId = event.ui_element.object_ids[-1]
                # Check if a button in the navigation bar was pressed
                if objectId in ["#Nav_Properties","#Nav_File","#Nav_Run","#Nav_Help"]: # If a navigation button was pressed
                    ChangeMainWindowSection(sharedMemory,root,objectId)

                # Check if a tool button in the toolbar was selected
                elif objectId in ["#Select","#Move_Camera","#Move_Node","#Create"]:
                    #The tool id is the unique object id of each button which will correspond to each tool
                    sharedMemory["SelectedTool"] = objectId

                # Zoom in and out buttons:
                elif objectId in ["#Zoom_In","#Zoom_Out"]:
                    ZoomButton(sharedMemory,objectId,scaleSpeed,scaleBounds)
                    changePersp = True
                # Deletes the selected object when the delete button is pressed
                elif objectId == "#Delete" and sharedMemory["Selected"]:
                    # Calls the destroy function on the associated edge/node
                    Delete(sharedMemory["Selected"],sharedMemory)
                    sharedMemory["Selected"] = None
                elif objectId in ["#Undo","#Redo"]:
                    #Undo/Redo an action if one of their respective buttons is pressed
                    [Undo,Redo][objectId == "#Redo"](sharedMemory)
                elif objectId == "#Home":
                    # Set the camera position back to the origin
                    sharedMemory["CameraPosition"] = Vector2(0,0)
                    # The camera has moved and so grid will be updated
                    changePersp = True
                elif objectId == "#Save":
                    # Don't allow saving files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory,mainUIManager,"Quit Algorithm Visualisation To Save","Please quit the algorithm visualisation first to save this graph")
                        continue
                    Save(sharedMemory,sharedMemory["SaveDir"] == None)
                elif objectId == "#Save_As":
                    # Don't allow saving files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory,mainUIManager,"Quit Algorithm Visualisation To Save","Please quit the algorithm visualisation first to save to a new graph")
                        continue
                    # Remove the save directory so a new one can be set
                    Save(sharedMemory,True)
                elif objectId == "#Open":
                    # Don't allow opening files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory,mainUIManager,"Quit Algorithm Visualisation To Open","Please quit the algorithm visualisation first to open a new graph")
                        continue
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory,mainUIManager,"Open Without Saving","Are you sure you want to open a new graph without saving?","#Save_Open_Prompt",actionButton="Yes")
                    else:
                        # Open a new file
                        Open(sharedMemory)
                        changePersp = True
                elif objectId == "#New":
                    # Don't allow new files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory,mainUIManager,"Quit Algorithm Visualisation To Create New","Please quit the algorithm visualisation first to create a new graph")
                        continue
                    # Check if the user wants to save their current graph if not already saved
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory,mainUIManager,"New Graph Without Saving","Are you sure you want to start a new graph without saving?","#Save_New_Prompt",actionButton="Yes")
                    else:
                        # Clear data
                        NewEnv(sharedMemory)
                        changePersp = True
                elif objectId == "#Quit":
                    # If the most recent version of the program has not been saved, prompt them to save it first
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory,mainUIManager,"Quit Without Saving","Are you sure you want to quit without saving?","#Save_Quit_Prompt",actionButton="Yes")
                    else:
                        Quit(sharedMemory)
                # Change and update the page displayed when next/back is pressed
                elif objectId == "#Next_Help":
                    sharedMemory["HelpPage"] += 1
                    UpdateHelpSection(root,sharedMemory)
                elif objectId == "#Back_Help":   
                    sharedMemory["HelpPage"] -= 1
                    UpdateHelpSection(root,sharedMemory)
                # Allow the user to select a start/end node for their SPA
                elif objectId in ["#Start_Node_Input","#End_Node_Input"]:
                    # Set the selected tool to a temporary tool
                    sharedMemory["SelectedTool"] = objectId
                # The button which will start the process for graph visualisation
                elif objectId == "#Start_Algorithm":
                    # Check that all properties have been entered and prompt the user that they must save their graph first
                    if sharedMemory["SPAStartNode"] == None or sharedMemory["SPAEndNode"] == None or sharedMemory["SPAEndNode"] == sharedMemory["SPAStartNode"]:
                        Prompt(sharedMemory,mainUIManager,"Invalid SPA Properties","Cannot perform a SPA without valid start and end nodes.")
                        continue
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory,mainUIManager,"Save Request","Please save your graph before running this algorithm.")
                        continue
                    if sharedMemory["SelectedSPA"] == None:
                        Prompt(sharedMemory,mainUIManager,"Invalid SPA Properties","Please choose a shortest path algorithm to perform.")
                        continue
                    # Check if the program is already in visualisation mode
                    if not sharedMemory["Edit"]:
                        # Undo all changes to the graph before proceeding
                        RestartSteps(sharedMemory,root,True)
                    if sharedMemory["SelectedSPA"] == "Dijkstra's Algorithm":
                        # Run the Dijkstra function
                        Dijkstra(sharedMemory,root)
                    elif sharedMemory["SelectedSPA"] == "A* Algorithm":
                        #Run the A* function
                        AStar(sharedMemory,root)
                    # Apply the first step to the environment
                    ApplyStep(sharedMemory,root)
                    
                elif objectId == "#Algorithm_Quit":
                    # Revert back to the original editing mode of the solution
                    sharedMemory["SelectedTool"] = "#Select"
                    sharedMemory["Edit"] = True
                    # Redisplay the regular toolbar and remove the explanation window
                    GetElement(root,"#Toolbar").show()
                    GetElement(root,"#Read_Only_Toolbar").hide()
                    GetElement(root,"#Explantion_Window").hide()
                    # Undo all changes to the graph
                    RestartSteps(sharedMemory,root,True)
                    for node in sharedMemory["Nodes"]:
                        node.UpdateLabel(sharedMemory)
                # Go to next step
                elif objectId == "#Step_Forward":
                    ApplyStep(sharedMemory,root,1)
                # Go to previous step
                elif objectId == "#Step_Backward":
                    ApplyStep(sharedMemory,root,-1)
                elif objectId == "#Skip_Forward":
                    SkipSteps(sharedMemory,root)
                elif objectId == "#Skip_Backward":
                    RestartSteps(sharedMemory,root)

            # Update the text when the slider moves
            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                # Record the slider which is currently being moved
                selectedSlider = GetElement(root,".".join(event.ui_element.object_ids))
                # Update the value displayed in the connected UI textbox
                UpdateSliderText(event.ui_element,event.value)
            # Update the text and slider
            elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                # Get the text and objectId of the textbox to process the event
                text = event.text
                objectId = event.ui_element.object_ids[-1]
                variable = None
                value = None
                # Update variables and sliders
                if objectId == "#Edge_Weight_Input_Box":
                    #Update the slider and return a validated value
                    value = UpdateSlider(event.ui_element,text)
                    variable = "weight"
                elif objectId == "#Edge_Length_Input_Box":
                    #Update the slider and return a validated value
                    value = UpdateSlider(event.ui_element,text)   
                    variable = "length"
                elif objectId in ["#Node_Name_Input","#Edge_Name_Input"]:
                    value = text
                    variable = "name"
                elif objectId in ["#Node_Colour_Input","#Edge_Colour_Input"]:
                    value = "#"+text
                    #Ensure the value is a valid size
                    variable = "colour"
                    if len(value) != 7:
                        variable = None
                # If a variable related text box was changed, a change property event should be called
                if variable != None:
                    sharedMemory["Changed"] = True
                    ChangeProperty(sharedMemory,object = sharedMemory["Selected"],attr = variable,value = value)              
            # Adjust scale with mouse wheel movement
            elif event.type == pygame.MOUSEWHEEL and not CheckHover(root,timedelta):
                ZoomWheel(event,sharedMemory,scaleSpeed,scaleBounds)
                changePersp = True
            # Handle mouse button press
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if sharedMemory["SelectedTool"] == "#Select" and not CheckHover(root,timedelta):
                    # Update the currently selected edge/node
                    selected = Select(sharedMemory,event.pos)
                    if selected:
                        UpdateSelection(sharedMemory,selected)
                        sharedMemory["Drag"] = True
                
                elif sharedMemory["SelectedTool"] in ["#Start_Node_Input","#End_Node_Input"] and not CheckHover(root,timedelta):
                    # Check if the user selected a node
                    selected = Select(sharedMemory,event.pos)
                    if type(selected) != Node:
                        # Reset the tool
                        sharedMemory["SelectedTool"] = "#Move_Camera"
                        continue
                    if sharedMemory["SelectedTool"] == "#Start_Node_Input":
                        # Set the starting node to the id of the selected node. 
                        sharedMemory["SPAStartNode"] = selected.id
                    else:
                        # Set the end node to the id of the selected node. 
                        sharedMemory["SPAEndNode"] = selected.id
                    # Reset the tool
                    sharedMemory["SelectedTool"] = "#Move_Camera"
            #Create a Node/Edge when the create tool is selected and not clicking on UI
                elif sharedMemory["SelectedTool"] == "#Create" and not CheckHover(root,timedelta) and sharedMemory["Edit"]:
                    selected = Select(sharedMemory,event.pos)
                    if type(selected) == Node:
                        # Start creating an edge from a starting node and select this node
                        edgeStart = selected
                        UpdateSelection(sharedMemory,selected)
                    elif type(selected) == Edge:
                        #Select the edge
                        UpdateSelection(sharedMemory,selected)
                    else:
                        sharedMemory["Changed"] = True
                        # Create a node if nothing was selected
                        pos = ScnToEnv(event.pos,sharedMemory)
                        operation = CreateNodeOperation(sharedMemory,position = pos)
                        #Select this node
                        UpdateSelection(sharedMemory,operation.node)
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not CheckHover(root,timedelta):
                selected = Select(sharedMemory,event.pos)
                sharedMemory["Drag"] = False
                # If a different node has been selected upon release of the user's cursor and the edge doesnt exist
                if type(selected) == Node and selected != edgeStart and edgeStart != None and selected not in edgeStart.connectedNodes:
                    sharedMemory["Changed"] = True
                    # Create a node between the two edges
                    operation = CreateEdgeOperation(sharedMemory,nodeA = edgeStart,nodeB = selected)
                    # Select this edge
                    UpdateSelection(sharedMemory,operation.edge)
                edgeStart = None
            # Dont allow any of the following events be executed if program is in readonly mode
            if not sharedMemory["Edit"]:
                mainUIManager.process_events(event)
                envUIManager.process_events(event)
                continue
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and selectedSlider != None:
                # Update the value of a slider when the user has been moving a slider and release their cursor
                objectId = selectedSlider.object_ids[-1]
                value = selectedSlider.get_current_value()
                variable = None
                # Map the object id onto a variable in the edge
                if objectId == "#Edge_Weight_Input":
                    variable = "weight"
                if objectId == "#Edge_Length_Input":
                    variable = "length"
                if variable != None:
                    # If a variable was mapped, change the value on the graph
                    sharedMemory["Changed"] = True
                    ChangeProperty(sharedMemory,object = sharedMemory["Selected"],attr = variable,value = value)
                selectedSlider = None
            elif event.type == pygame.KEYDOWN:
                # Delete the selected object if the delete key is pressed
                if event.key == pygame.K_DELETE and sharedMemory["Selected"]:
                    sharedMemory["Changed"] = True
                    # Calls the destroy function on the associated edge/node
                    Delete(sharedMemory["Selected"],sharedMemory)
                # Check if Ctrl + Z or Ctrl + Y has been pressed
                elif event.key in [pygame.K_y,pygame.K_z] and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    sharedMemory["Changed"] = True
                    # Undo/Redo functions called for their respective buttons
                    [Undo,Redo][event.key == pygame.K_y](sharedMemory)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    Save(sharedMemory,True)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    Save(sharedMemory,sharedMemory["SaveDir"] == None)
            
            # Run pygame_gui builtin function which finalises event processing
            mainUIManager.process_events(event)
            envUIManager.process_events(event)

        # Update the node paramaters for the SPA properties
        UpdateSPProperties(root,sharedMemory)

        # Drag a selected node to towards the mouse position
        if sharedMemory["Drag"] and type(sharedMemory["Selected"]) == Node:
            sharedMemory["Selected"].DragToward(ScnToEnv(sharedMemory["MousePosition"],sharedMemory),sharedMemory)
        # Check if the camera needs to be moved
        changePersp = changePersp or MoveCamera(root,timedelta,mouseStates,sharedMemory)

        # Adjust nodes
        NodeReadjustment(sharedMemory,timedelta)

        # Update the grid when the camera position / scale changes
        if changePersp:
            grid = CreateGrid(screen,gridLineSpacing,sharedMemory)