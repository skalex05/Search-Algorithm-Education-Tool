from gui import *
from operations import ChangeProperty, CreateEdgeOperation, CreateNodeOperation, Delete
from functions import *
from algorithm import AStar, Dijkstra
from graph import Node, Edge, Save, Open
import webbrowser

if __name__ == "__main__":
    # ~~~ PROGRAM VARIABLES ~~~

    framerate = 60  # Set the maximum number of times the UI and environment will be updated per second
    gridLineSpacing = 100  # How far apart grid lines are generated
    scaleSpeed = 0.05  # The rate at which scale can change
    scaleBounds = (0.3, 1.6)  # Respective minimum/maximum scale values
    gridColour = (56, 61, 61)  # The rgb  colour of the gridlines
    bgColour = (210, 210, 210)  # Set the rgb background colour of the environment

    # Initialise a dictionary containing parameters which can be easily shared between functions
    sharedMemory = {
        "Run": True,  # This boolean will determine when all threads should close
        "CameraPosition": Vector2(0, 0),  # Represents the user's position in the environment
        "ScaleBounds": (0.3, 1.6),  # The scale of the environment must be contained to these bounds
        "Scale": scaleBounds[0],  # The scale in the environment view
        "ScreenSize": Vector2(pygame.display.get_desktop_sizes()[0]) - Vector2(0, 80),  # The size of the screen
        "MousePosition": Vector2(0, 0),  # Contains where the mouse currently is on screen
        "MouseMovement": Vector2(0, 0),  # Contains the relative movement of the mouse
        "SelectedTool": "#Select",  # The tool that should be used when the left click button is pressed
        "Selected": [],  # Represents the currently selected object
        "SelectionColour": "#00d0f9",  # The outline colour of selected nodes/edges
        "SaveDir": None,  # The default location used to save files
        "Changed": False,  # The graph has not been saved in this state
        "Drag": False,  # Denotes if the selected object should be dragged
        "UndoStack": [],  # A collection of operations that can be undone
        "RedoStack": [],  # A collection of operations that can be redone
        "Nodes": [],  # Contains all nodes in the environment
        "Edges": [],  # Contains all edges in the environment
        "LengthToUnitRatio": 25,  # One unit of length in an edge represents 25 units in the environment
        "MaxForce": 500,  # Maximum force which can be applied to nodes
        "AdjustmentRate": 200,  # The rate at which nodes connected by an edge move to reach their desired length
        "OptimalNodeDistance": 500,  # Distance disconnected nodes want to be from eachother
        "EdgeCount": 1,  # Counts the number of edges
        "NodeCount": 1,  # Counts the number of edges
        "HeuristicMultiplier": 0.008,  # A scale applied to the distance between nodes to calculate heuristic costs
        "HelpPage": 1,  # Page number of the help section
        "SPAStartNode": None,  # Stores the start node where a SPA will be performed
        "SPAEndNode": None,  # Stores the end node where a SPA will be performed
        "SPA": None,  # Stores the SPA that is being performed
        "SelectedSPA": None,  # The SPA the user has selected to be performed
        "Steps": [],
        # When an SPA is run on a graph, a set of steps are created to show how to calculate the shortest route
        "Step": 0,  # The index of the currently displayed step
        "Edit": True,  # Boolean which determines if the user can edit their graph
        "Defaults": {
            "NodeColour": "#f42e2e",
            "EdgeColour": "#5e6060",
            "EdgeWeight": 10,
            "EdgeLength": 10
        }
    }

    # ~~~ INITIALISATION ~~~

    # Generate the UI from gui.py and retrieve the pygame surface and GUI manager
    screen, mainUIManager, envUIManager = GenerateUI(sharedMemory["ScreenSize"])

    sharedMemory["MainUIManager"] = mainUIManager
    sharedMemory["EnvUIManager"] = envUIManager

    # Create a root variable for cleaner GetElement calls
    root = mainUIManager.get_root_container()

    # Create Environment Grid
    grid = CreateGrid(screen, gridLineSpacing, sharedMemory)

    # Object which will be responsible for managing the framerate/frametime of the UI
    clock = pygame.time.Clock()

    # UI Element used to display the FPS of the sol
    FPS = GetElement(root, "#FPS")

    # A variable used to represent the starting node of an edge to be created
    edgeStart = None
    selectionStart = None

    # Tracks which slider is currently being moved so that values can be adjusted upon its release
    selectedSlider = None

    UpdatePropertiesUI(sharedMemory)

    # Create a mainloop where the UI will be updated and user input will be processed
    while sharedMemory["Run"]:
        timedelta = clock.tick(
            framerate) / 1000  # Limit the framerate and retrieve the time in miliseconds since the last frame
        if timedelta != 0:
            GetElement(FPS, "#Label_Text").set_text(f"FPS: {int(1 / timedelta)}")

        # ~~~ NEW FRAME ~~~

        # Update all UI elements
        mainUIManager.update(timedelta)
        envUIManager.update(timedelta)

        # Clear the screen
        screen.fill(bgColour)

        # Render the grid
        for gridLine in grid:
            pygame.draw.line(screen, gridColour, *gridLine)

        # Render edges
        for edge in sharedMemory["Edges"]:
            edge.Draw(screen, sharedMemory)

        # If the user is trying to create an edge, a line is drawn between the cursor and starting node
        if edgeStart != None:
            pygame.draw.line(screen, sharedMemory["Defaults"]["EdgeColour"], EnvToScn(edgeStart.position, sharedMemory),
                             sharedMemory["MousePosition"], width=int(25 * sharedMemory["Scale"]))

        # Render nodes
        for node in sharedMemory["Nodes"]:
            node.Draw(screen, sharedMemory)

        # Render selection area

        if selectionStart != None:
            xBounds, yBounds = GetBounds(EnvToScn(selectionStart, sharedMemory), Vector2(pygame.mouse.get_pos()))
            start = Vector2(xBounds[0], yBounds[0])
            size = Vector2(xBounds[1], yBounds[1]) - start
            selectionRect = pygame.Rect(start, size)
            shapeSurface = pygame.Surface(selectionRect.size, pygame.SRCALPHA)
            pygame.draw.rect(shapeSurface, sharedMemory["SelectionColour"] + "44", shapeSurface.get_rect())
            screen.blit(shapeSurface, selectionRect)

        # Repaint the UI
        envUIManager.draw_ui(screen)
        mainUIManager.draw_ui(screen)

        # Update displayed pygame surface
        pygame.display.update()

        # Record the position of the mouse and its movement since the last frame
        sharedMemory["MousePosition"] = Vector2(pygame.mouse.get_pos())
        sharedMemory["MouseMovement"] = Vector2(pygame.mouse.get_rel())

        # Get which mouse buttons are currently held down
        mouseStates = pygame.mouse.get_pressed()

        # This boolean determines if the environment grid needs to be rebuilt in a new position
        # If the user leaves the camera in the same scale/position, the grid is not rebuilt each frame
        changePersp = False

        # ~~~ EVENT / INPUT PROCESSING ~~~

        for event in pygame.event.get():
            # ~~~ PYGAME EVENTS ~~~

            if event.type == pygame.QUIT:
                # If the most recent version of the program has not been saved, prompt them to save it first
                if sharedMemory["Changed"]:
                    Prompt(sharedMemory, mainUIManager, "Quit Without Saving",
                           "Are you sure you want to quit without saving?", "#Save_Quit_Prompt", actionButton="Yes")
                else:
                    Quit(sharedMemory)

            elif event.type == pygame.VIDEORESIZE:
                # Update the size of the screen
                size = (event.w, event.h)
                envUIManager.set_window_resolution(size)
                mainUIManager.set_window_resolution(size)
                sharedMemory["ScreenSize"] = Vector2(size)
                changePersp = True

            # Adjust scale with mouse wheel movement
            elif event.type == pygame.MOUSEWHEEL and not CheckHover(root, timedelta):
                ZoomWheel(event, sharedMemory, scaleSpeed, scaleBounds)
                changePersp = True

            # Handle mouse button presses
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                selected = Select(sharedMemory, event.pos)
                if sharedMemory["SelectedTool"] == "#Select" and not CheckHover(root, timedelta) and selected != None:
                    # Update the currently selected edge/node
                    UpdateSelection(sharedMemory, [selected])
                    sharedMemory["Drag"] = True
                elif sharedMemory["SelectedTool"] == "#Select" and not CheckHover(root, timedelta):
                    selectionStart = ScnToEnv(event.pos, sharedMemory)

                elif sharedMemory["SelectedTool"] in ["#Start_Node_Input", "#End_Node_Input"] and not CheckHover(root,
                                                                                                                 timedelta):
                    # Check if the user selected a node
                    selected = Select(sharedMemory, event.pos)
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

                # Create a Node/Edge when the create tool is selected and not clicking on UI
                elif sharedMemory["SelectedTool"] == "#Create" and not CheckHover(root, timedelta) and sharedMemory[
                    "Edit"]:
                    selected = Select(sharedMemory, event.pos)
                    if type(selected) == Node:
                        # Start creating an edge from a starting node and select this node
                        edgeStart = selected
                        UpdateSelection(sharedMemory, [selected])
                    elif type(selected) == Edge:
                        # Select the edge
                        UpdateSelection(sharedMemory, [selected])
                    else:
                        sharedMemory["Changed"] = True
                        # Create a node if nothing was selected
                        pos = ScnToEnv(event.pos, sharedMemory)
                        operation = CreateNodeOperation(sharedMemory, position=pos)
                        # Select this node
                        UpdateSelection(sharedMemory, [operation.node])

            # Handle when the left mouse button is released
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                selected = Select(sharedMemory, event.pos)
                if not CheckHover(root, timedelta):
                    # If a different node has been selected upon release of the user's cursor and the edge doesnt exist
                    if type(selected) == Node and selected != edgeStart and edgeStart != None and selected not in edgeStart.connectedNodes:
                        sharedMemory["Changed"] = True
                        # Create a node between the two edges
                        operation = CreateEdgeOperation(sharedMemory, nodeA=edgeStart, nodeB=selected)
                        # Select this edge
                        UpdateSelection(sharedMemory, [operation.edge])
                if selectionStart != None:
                    UpdateSelection(sharedMemory,
                                    SelectArea(sharedMemory, selectionStart, ScnToEnv(event.pos, sharedMemory)))
                sharedMemory["Drag"] = False
                selectionStart = None
                edgeStart = None
                if selectedSlider != None and sharedMemory["Edit"]:
                    # Update the value of a slider when the user has been moving a slider and release their cursor
                    if sharedMemory["Selected"] != []:
                        objectId = selectedSlider.object_ids[-1]
                        value = selectedSlider.get_current_value()
                        variable = None
                        for item in sharedMemory["Selected"]:
                            if type(item) == Node:
                                continue
                            # Map the object id onto a variable in the edge
                            if objectId in ["#Edge_Weight_Input", "#Default_Weight_Input"]:
                                variable = "weight"
                            if objectId in ["#Edge_Length_Input", "#Default_Length_Input"]:
                                variable = "length"
                            if variable != None:
                                # If a variable was mapped, change the value on the graph
                                sharedMemory["Changed"] = True
                                ChangeProperty(sharedMemory, object=item, attr=variable, value=value)
                    else:
                        objectId = selectedSlider.object_ids[-1]
                        value = selectedSlider.get_current_value()
                        if objectId == "#Default_Length_Input":
                            sharedMemory["Defaults"]["EdgeLength"] = value
                        elif objectId == "#Default_Weight_Input":
                            sharedMemory["Defaults"]["EdgeWeight"] = value
                    selectedSlider = None

            # Delete the selected object if the delete key is pressed
            elif event.type == pygame.KEYDOWN and sharedMemory["Edit"]:
                if event.key == pygame.K_DELETE:
                    sharedMemory["Changed"] = True
                    # Calls the destroy function on each associated edge/node
                    for item in sharedMemory["Selected"]:
                        Delete(item, sharedMemory)
                    sharedMemory["Selected"] = []
                # Check if Ctrl + Z or Ctrl + Y has been pressed
                elif event.key in [pygame.K_y, pygame.K_z] and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    sharedMemory["Changed"] = True
                    # Undo/Redo functions called for their respective buttons
                    [Undo, Redo][event.key == pygame.K_y](sharedMemory)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    Save(sharedMemory, True)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    Save(sharedMemory, sharedMemory["SaveDir"] == None)

            # Process a dialogue confirmation depending on its id
            elif event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
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
                    success = Open(sharedMemory)
                    # If the file could not be opened, prompt the user
                    if not success:
                        Prompt(sharedMemory, mainUIManager, "File Could Not Be Opened",
                               "Your file could not be opened. This may be because the file has become corrupted")
                    changePersp = True

            # Process each button press respectively
            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                # Get the most specific objectId about an element
                objectId = event.ui_element.object_ids[-1]
                # Check if a button in the navigation bar was pressed
                if objectId in ["#Nav_Properties", "#Nav_File", "#Nav_Run",
                                "#Nav_Help"]:  # If a navigation button was pressed
                    ChangeMainWindowSection(sharedMemory, root, objectId)

                # Check if a tool button in the toolbar was selected
                elif objectId in ["#Select", "#Move_Camera", "#Move_Node", "#Create"]:
                    # The tool id is the unique object id of each button which will correspond to each tool
                    sharedMemory["SelectedTool"] = objectId

                # Zoom in and out buttons:
                elif objectId in ["#Zoom_In", "#Zoom_Out"]:
                    ZoomButton(sharedMemory, objectId, scaleSpeed, scaleBounds)
                    changePersp = True

                # Deletes the selected object when the delete button is pressed
                elif objectId == "#Delete":
                    # Calls the destroy function on the associated edge/node
                    for item in sharedMemory["Selected"]:
                        Delete(item, sharedMemory)
                    sharedMemory["Selected"] = []

                # Undo/Redo an action if one of their respective buttons is pressed
                elif objectId in ["#Undo", "#Redo"]:
                    [Undo, Redo][objectId == "#Redo"](sharedMemory)

                # Set the camera position back to the origin
                elif objectId == "#Home":

                    sharedMemory["CameraPosition"] = Vector2(0, 0)
                    sharedMemory["Scale"] = sharedMemory["ScaleBounds"][0]
                    # The camera has moved and so grid will be updated
                    changePersp = True

                # Attempt to save a file without file dialogue
                elif objectId == "#Save":
                    # Don't allow saving files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory, mainUIManager, "Quit Algorithm Visualisation To Save",
                               "Please quit the algorithm visualisation first to save this graph")
                        continue
                    Save(sharedMemory, sharedMemory["SaveDir"] == None)

                # Attempt to save a file and prompt the user to enter a directory
                elif objectId == "#Save_As":
                    # Don't allow saving files to be created when visualising
                    if sharedMemory["Edit"]:
                        # Remove the save directory so a new one can be set
                        Save(sharedMemory, True)
                    else:
                        Prompt(sharedMemory, mainUIManager, "Quit Algorithm Visualisation To Save",
                               "Please quit the algorithm visualisation first to save to a new graph")

                # Attempt to open a file 
                elif objectId == "#Open":
                    # Don't allow opening files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory, mainUIManager, "Quit Algorithm Visualisation To Open",
                               "Please quit the algorithm visualisation first to open a new graph")
                    # Don't allow opening files if there is an unsaved change to the user's current graph
                    elif sharedMemory["Changed"]:
                        Prompt(sharedMemory, mainUIManager, "Open Without Saving",
                               "Are you sure you want to open a new graph without saving?", "#Save_Open_Prompt",
                               actionButton="Yes")
                    else:
                        # Open a new file
                        success = Open(sharedMemory)
                        # If the file could not be opened, prompt the user
                        if not success:
                            Prompt(sharedMemory, mainUIManager, "File Could Not Be Opened",
                                   "Your file could not be opened. This may be because the file has become corrupted")
                        else:
                            changePersp = True

                elif objectId == "#New":
                    # Don't allow new files to be created when visualising
                    if not sharedMemory["Edit"]:
                        Prompt(sharedMemory, mainUIManager, "Quit Algorithm Visualisation To Create New",
                               "Please quit the algorithm visualisation first to create a new graph")
                    # Check if the user wants to save their current graph if not already saved
                    elif sharedMemory["Changed"]:
                        Prompt(sharedMemory, mainUIManager, "New Graph Without Saving",
                               "Are you sure you want to start a new graph without saving?", "#Save_New_Prompt",
                               actionButton="Yes")
                    else:
                        # Clear data
                        NewEnv(sharedMemory)
                        changePersp = True

                elif objectId == "#Quit":
                    # If the most recent version of the program has not been saved, prompt them to save it first
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory, mainUIManager, "Quit Without Saving",
                               "Are you sure you want to quit without saving?", "#Save_Quit_Prompt", actionButton="Yes")
                    else:
                        Quit(sharedMemory)

                # Change and update the page displayed when next/back is pressed
                elif objectId == "#Next_Help":
                    sharedMemory["HelpPage"] += 1
                    UpdateHelpSection(root, sharedMemory)

                elif objectId == "#Back_Help":
                    sharedMemory["HelpPage"] -= 1
                    UpdateHelpSection(root, sharedMemory)

                # Allow the user to select a start/end node for their SPA
                elif objectId in ["#Start_Node_Input", "#End_Node_Input"]:
                    # Set the selected tool to a temporary tool
                    sharedMemory["SelectedTool"] = objectId

                # The button which will start the process for graph visualisation
                elif objectId == "#Start_Algorithm":
                    # Check that all properties have been entered and prompt the user that they must save their graph first
                    if sharedMemory["SPAStartNode"] == None or sharedMemory["SPAEndNode"] == None or sharedMemory[
                        "SPAEndNode"] == sharedMemory["SPAStartNode"]:
                        Prompt(sharedMemory, mainUIManager, "Invalid SPA Properties",
                               "Cannot perform a SPA without valid start and end nodes.")
                        continue
                    if sharedMemory["Changed"]:
                        Prompt(sharedMemory, mainUIManager, "Save Request",
                               "Please save your graph before running this algorithm.")
                        continue
                    if sharedMemory["SelectedSPA"] == None:
                        Prompt(sharedMemory, mainUIManager, "Invalid SPA Properties",
                               "Please choose a shortest path algorithm to perform.")
                        continue
                    # Check if the program is already in visualisation mode
                    if not sharedMemory["Edit"]:
                        # Undo all changes to the graph before proceeding
                        RestartSteps(sharedMemory, root, True)
                    if sharedMemory["SelectedSPA"] == "Dijkstra's Algorithm":
                        # Run the Dijkstra function
                        Dijkstra(sharedMemory, root)
                    elif sharedMemory["SelectedSPA"] == "A* Algorithm":
                        # Run the A* function
                        AStar(sharedMemory, root)
                    # Apply the first step to the environment
                    ApplyStep(sharedMemory, root)

                elif objectId == "#Algorithm_Quit":
                    # Revert back to the original editing mode of the solution
                    sharedMemory["SelectedTool"] = "#Select"
                    sharedMemory["Edit"] = True
                    # Redisplay the regular toolbar and remove the explanation window
                    GetElement(root, "#Toolbar").show()
                    GetElement(root, "#Read_Only_Toolbar").hide()
                    GetElement(root, "#Explantion_Window").hide()
                    # Undo all changes to the graph
                    RestartSteps(sharedMemory, root, True)
                    for node in sharedMemory["Nodes"]:
                        node.UpdateLabel(sharedMemory)
                # Go to next step
                elif objectId == "#Step_Forward":
                    ApplyStep(sharedMemory, root, 1)

                # Go to previous step
                elif objectId == "#Step_Backward":
                    ApplyStep(sharedMemory, root, -1)

                # Skip to the final step
                elif objectId == "#Skip_Forward":
                    SkipSteps(sharedMemory, root)

                # Return to the first step
                elif objectId == "#Skip_Backward":
                    RestartSteps(sharedMemory, root)
            # Update the text when the slider moves
            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                # Record the slider which is currently being moved
                selectedSlider = GetElement(root, ".".join(event.ui_element.object_ids))
                # Update the value displayed in the connected UI textbox
                UpdateSliderText(event.ui_element, event.value)
            elif event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
                if event.link_target.startswith("pg:"):
                    sharedMemory["HelpPage"] = int(event.link_target[3::])
                    UpdateHelpSection(root, sharedMemory)
                else:
                    webbrowser.get().open(event.link_target)

            # Update the text and slider
            elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                # Get the text and objectId of the textbox to process the event
                text = event.text
                objectId = event.ui_element.object_ids[-1]
                if len(sharedMemory["Selected"]) == 1:
                    variable = None
                    value = None
                    # Update variables and sliders
                    if objectId == "#Edge_Weight_Input_Box":
                        # Update the slider and return a validated value
                        value = UpdateSlider(event.ui_element, text)
                        variable = "weight"
                    elif objectId == "#Edge_Length_Input_Box":
                        # Update the slider and return a validated value
                        value = UpdateSlider(event.ui_element, text)
                        variable = "length"
                    elif objectId in ["#Node_Name_Input", "#Edge_Name_Input"]:
                        value = text
                        variable = "name"
                    elif objectId in ["#Node_Colour_Input", "#Edge_Colour_Input"]:
                        value = "#" + text
                        # Ensure the value is a valid size
                        variable = "colour"
                        if len(value) != 7:
                            variable = None
                    # If a variable related text box was changed, a change property event should be called
                    if variable != None:
                        sharedMemory["Changed"] = True
                        ChangeProperty(sharedMemory, object=sharedMemory["Selected"][0], attr=variable, value=value)
                elif len(sharedMemory["Selected"]) > 1:
                    variable = None
                    value = None
                    # Update variables and sliders
                    if objectId == "#Default_Weight_Input_Box":
                        # Update the slider and return a validated value
                        value = UpdateSlider(event.ui_element, text)
                        variable = "weight"
                    elif objectId == "#Default_Length_Input_Box":
                        # Update the slider and return a validated value
                        value = UpdateSlider(event.ui_element, text)
                        variable = "length"
                    elif objectId in ["#Default_Node_Colour_Input", "#Default_Edge_Colour_Input"]:
                        value = "#" + text
                        # Ensure the value is a valid size
                        variable = "colour"
                        if len(value) != 7:
                            variable = None
                    for item in sharedMemory["Selected"]:
                        # If a variable related text box was changed, a change property event should be called
                        if (variable in ["weight", "length"] or objectId == "#Default_Edge_Colour_Input" and type(
                                item) == Edge) or (
                                variable == "colour" and objectId == "#Default_Node_Colour_Input" and type(
                                item) == Node):
                            sharedMemory["Changed"] = True
                            ChangeProperty(sharedMemory, object=item, attr=variable, value=value)
                else:
                    if objectId == "#Default_Node_Colour_Input":
                        if len(text) == 6:
                            sharedMemory["Defaults"]["NodeColour"] = "#" + text
                    elif objectId == "#Default_Edge_Colour_Input":
                        if len(text) == 6:
                            sharedMemory["Defaults"]["EdgeColour"] = "#" + text
                    elif objectId == "#Default_Weight_Input_Box":
                        value = UpdateSilder(event.ui_element, text)
                        sharedMemory["Defaults"]["EdgeWeight"] = value
                    elif objectId == "#Default_Length_Input_Box":
                        value = UpdateSilder(event.ui_element, text)
                        sharedMemory["Defaults"]["EdgeLength"] = value

            # Update the chosen SPA
            elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
                sharedMemory["SelectedSPA"] = event.text

            # Run pygame_gui builtin function which finalises event processing
            mainUIManager.process_events(event)
            envUIManager.process_events(event)

        # Update the node paramaters for the SPA properties
        UpdateSPProperties(root, sharedMemory)

        # Drag a selected node to towards the mouse position
        if sharedMemory["Drag"] and sharedMemory["Selected"] != [] and type(sharedMemory["Selected"][0]) == Node:
            sharedMemory["Selected"][0].DragToward(ScnToEnv(sharedMemory["MousePosition"], sharedMemory), sharedMemory)
        # Check if the camera needs to be moved
        changePersp = changePersp or MoveCamera(root, timedelta, mouseStates, sharedMemory)

        # Adjust nodes
        NodeReadjustment(sharedMemory, timedelta)

        # Update the grid when the camera position / scale changes
        if changePersp:
            grid = CreateGrid(screen, gridLineSpacing, sharedMemory)
