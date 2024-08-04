# A list of functions specialised for generating the program's UI

import pygame
import pygame_gui
from pygame_gui.elements import UIPanel,UIButton,UITextEntryLine,UIHorizontalSlider,UILabel,UIImage,UITextBox,UISelectionList
from pygame_gui.core import ObjectID, UIContainer
from pygame_gui.windows import UIConfirmationDialog
from pygame.math import Vector2
from functions import CreateUIElement
import string
import json

pygame.init()

# Anchors - Anchor elements to a corner of the screen
TOP_RIGHT = [{"right":"right","left":"right"},"topright"]
TOP_LEFT = [{"right":"left","left":"left"},"topleft"]
BOTTOM_RIGHT = [{"right":"right","left":"right","top":"bottom","bottom":"bottom"},"bottomright"]
BOTTOM_LEFT = [{"right":"left","left":"left","top":"bottom","bottom":"bottom"},"bottomleft"]    


# ~~~ MAIN UI PANEL ~~~
# This UI panel will contain all information regarding to:
# - Graph Properties
# - File Options
# - Shortest Path Algorithm Parameters
# - Help
# A navigation bar will be used to move between each section

# Create a navigation bar at the top of the main window so the user can navigate between each section
def CreateNavigationBar(manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight):
    # Navigation bar and all of its associated buttons:
    navBar = CreateUIElement(manager,UIPanel,(-3,-3),(400,navHeight),TOP_LEFT,
                    starting_height = 2, object_id = ObjectID(object_id = "#Navigation_Bar",class_id="@Button_Bar"),container = mainWindow)
    buttonSize = (navHeight,navHeight)
    
    CreateUIElement(manager,UIButton,(0,0),buttonSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Nav_Properties",class_id = "@Button_Bar"),container = navBar,text="")
    CreateUIElement(manager,UIButton,(navHeight,0),buttonSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Nav_File",class_id = "@Button_Bar"),container = navBar,text="")
    CreateUIElement(manager,UIButton,(navHeight*2,0),buttonSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Nav_Run",class_id = "@Button_Bar"),container = navBar,text="")
    CreateUIElement(manager,UIButton,(navHeight*3,0),buttonSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Nav_Help",class_id = "@Button_Bar"),container = navBar,text="")

# Creates two UI subsections to display properties of nodes and edges
def CreateProperties(manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight,visible = True):
    # There will be two properties pages; one for nodes and another for edges
    properties = CreateUIElement(manager,UIPanel,(-2,navHeight),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Properties"),container = mainWindow,visible = visible)
    nodeProperties = CreateUIElement(manager,UIPanel,(0,0),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Node_Properties"),container = properties,visible = False)
    edgeProperties = CreateUIElement(manager,UIPanel,(0,0),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Edge_Properties"),container = properties,visible = False)
    defaultProperties = CreateUIElement(manager,UIPanel,(0,0),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Default_Properties"),container = properties,visible = False)
    
    # Node Properties:
    CreateUIElement(manager,UILabel,(10,10),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Node_Name_Label",class_id="@LeftAlignedText"),container = nodeProperties,text = "Name:")
    nodeNameInput = CreateUIElement(manager,UITextEntryLine,(110,10),(200,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Node_Name_Input"),container = nodeProperties)
    nodeNameInput.set_text_length_limit(15)
    CreateUIElement(manager,UILabel,(10,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Node_Colour_Label",class_id="@LeftAlignedText"),container = nodeProperties,text = "Colour: #")
    nodeColourInput = CreateUIElement(manager,UITextEntryLine,(110,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Node_Colour_Input"),container = nodeProperties)
    nodeColourInput.set_text_length_limit(6)
    nodeColourInput.set_allowed_characters([*string.hexdigits]) #Colour input will be hexadecimal in the form FFFFFF for example

    # Edge Properties:
    CreateUIElement(manager,UILabel,(10,10),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Name_Label",class_id="@LeftAlignedText"),container = edgeProperties,text = "Name:")
    edgeNameInput = CreateUIElement(manager,UITextEntryLine,(110,10),(200,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Name_Input"),container = edgeProperties)
    edgeNameInput.set_text_length_limit(15)
    CreateUIElement(manager,UILabel,(10,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Colour_Label",class_id="@LeftAlignedText"),container = edgeProperties,text = "Colour: #")
    edgeColourInput = CreateUIElement(manager,UITextEntryLine,(110,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Colour_Input"),container = edgeProperties)
    edgeColourInput.set_text_length_limit(6)
    edgeColourInput.set_allowed_characters([*string.hexdigits])

    CreateUIElement(manager,UILabel,(10,10+fieldHeight*2),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Weight_Label",class_id="@LeftAlignedText"),container = edgeProperties,text = "Weight:")
    CreateUIElement(manager,UIHorizontalSlider,(110,10+fieldHeight*2.25),(200,fieldHeight/2),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Weight_Input"),container = edgeProperties,start_value = 0,value_range = (0,100))
    edgeWeightTInput = CreateUIElement(manager,UITextEntryLine,(310,10+fieldHeight*2),(80,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Weight_Input_Box"),container = edgeProperties)
    edgeWeightTInput.set_text("0")
    edgeWeightTInput.set_text_length_limit(3)
    edgeWeightTInput.set_allowed_characters("numbers")

    CreateUIElement(manager,UILabel,(10,10+fieldHeight*3),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Length_Label",class_id="@LeftAlignedText"),container = edgeProperties,text = "Length:")
    CreateUIElement(manager,UIHorizontalSlider,(110,10+fieldHeight*3.25),(200,fieldHeight/2),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Length_Input"),container = edgeProperties,start_value = 10,value_range = (5,25))
    edgeLengthTInput = CreateUIElement(manager,UITextEntryLine,(310,10+fieldHeight*3),(80,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_Length_Input_Box"),container = edgeProperties)
    edgeLengthTInput.set_text("0")
    edgeLengthTInput.set_text_length_limit(3)
    edgeLengthTInput.set_allowed_characters("numbers")
    
    # Default Properties:
    CreateUIElement(manager,UILabel,(10,10),(120,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Node_Colour_Label",class_id="@LeftAlignedText"),container = defaultProperties,text = "Node Colour: #")
    nodeColourInput = CreateUIElement(manager,UITextEntryLine,(140,10),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Node_Colour_Input"),container = defaultProperties)
    nodeColourInput.set_text_length_limit(6)
    nodeColourInput.set_allowed_characters([*string.hexdigits])
    
    CreateUIElement(manager,UILabel,(10,10+fieldHeight),(120,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Edge_Colour_Label",class_id="@LeftAlignedText"),container = defaultProperties,text = "Edge Colour: #")
    edgeColourInput = CreateUIElement(manager,UITextEntryLine,(140,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Edge_Colour_Input"),container = defaultProperties)
    edgeColourInput.set_text_length_limit(6)
    edgeColourInput.set_allowed_characters([*string.hexdigits])
    
    
    CreateUIElement(manager,UILabel,(10,10+fieldHeight*2),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Weight_Label",class_id="@LeftAlignedText"),container = defaultProperties,text = "Weight:")
    CreateUIElement(manager,UIHorizontalSlider,(110,10+fieldHeight*2.25),(200,fieldHeight/2),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Weight_Input"),container = defaultProperties,start_value = 0,value_range = (0,100))
    edgeWeightTInput = CreateUIElement(manager,UITextEntryLine,(310,10+fieldHeight*2),(80,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Weight_Input_Box"),container = defaultProperties)
    edgeWeightTInput.set_text("0")
    edgeWeightTInput.set_text_length_limit(3)
    edgeWeightTInput.set_allowed_characters("numbers")

    CreateUIElement(manager,UILabel,(10,10+fieldHeight*3),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Length_Label",class_id="@LeftAlignedText"),container = defaultProperties,text = "Length:")
    CreateUIElement(manager,UIHorizontalSlider,(110,10+fieldHeight*3.25),(200,fieldHeight/2),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Length_Input"),container = defaultProperties,start_value = 10,value_range = (5,25))
    edgeLengthTInput = CreateUIElement(manager,UITextEntryLine,(310,10+fieldHeight*3),(80,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Default_Length_Input_Box"),container = defaultProperties)
    edgeLengthTInput.set_text("0")
    edgeLengthTInput.set_text_length_limit(3)
    edgeLengthTInput.set_allowed_characters("numbers")

# This is a collection of all buttons the user can interact with to save/load/create new graphs as well as quit
def CreateFileOptions(manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight,visible = False):
    fileOptions = CreateUIElement(manager,UIPanel,(-2,navHeight),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#File_Options"),container = mainWindow,visible = visible)
    CreateUIElement(manager,UIButton,(15,10),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#New"),container = fileOptions,text="New")
    CreateUIElement(manager,UIButton,(15,10+fieldHeight),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Save"),container = fileOptions,text="Save")
    CreateUIElement(manager,UIButton,(15,10+fieldHeight*2),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Save_As"),container = fileOptions,text="Save As")
    CreateUIElement(manager,UIButton,(15,10+fieldHeight*3),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Open"),container = fileOptions,text="Open")
    CreateUIElement(manager,UIButton,(15,10+fieldHeight*4),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Quit"),container = fileOptions,text="Quit")

# This UI will allow the user to enter parameters for a chosen pathfinding algorithm
# The user will then be able to run the algorithm from this window
def CreateSPProperties(manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight,algorithms,visible = False):
    properties = CreateUIElement(manager,UIPanel,(-2,navHeight),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#SPProperties"),container = mainWindow,visible = visible)
    CreateUIElement(manager,UILabel,(10,10),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Start_Node_Label",class_id="@LeftAlignedText"),container = properties,text = "Start Node:")
    CreateUIElement(manager,UIButton,(110,10),(150,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Start_Node_Input"),container = properties,text="Select A Node")  
    CreateUIElement(manager,UILabel,(10,10+fieldHeight),(100,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#End_Node_Label",class_id="@LeftAlignedText"),container = properties,text = "End Node:")
    CreateUIElement(manager,UIButton,(110,10+fieldHeight),(150,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#End_Node_Input"),container = properties,text="Select A Node")
    CreateUIElement(manager,UILabel,(15,10+fieldHeight*3),(winWidth-30,fieldHeight),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Select_Label"),container = properties,text = "Select an algorithm:")
    CreateUIElement(manager,UISelectionList,(15,10+fieldHeight*4),(winWidth-30,35*len(algorithms)),TOP_LEFT,
                    object_id = ObjectID(object_id = "#SPA_Selection_List"),container = properties,item_list = algorithms)

    CreateUIElement(manager,UIButton,(15,10-fieldHeight),(winWidth-30,fieldHeight),BOTTOM_LEFT,
                    object_id = ObjectID(object_id = "#Start_Algorithm"),container = properties,text="Start")

# The help page will consist of forward and back buttons, text explanations and visual guide to explain how to use the software
def CreateHelp(manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight,imageSize = 200,visible = False):
    helpPanel = CreateUIElement(manager,UIPanel,(-2,navHeight),(winWidth,winHeight-navHeight),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Help"),container = mainWindow,visible = visible)
    #Load the json file for the help information
    helpInfo = json.load(open("help.json","r"))
    #Load the first image and text for the help section
    image = pygame.image.load(helpInfo["image"]["1"])
    text = helpInfo["explanation"]["1"]
    CreateUIElement(manager,UIImage,(15,10),(winWidth-30,imageSize),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Help_Image"),container = helpPanel,image_surface = image)
    CreateUIElement(manager,UITextBox,(15,210),(winWidth-30,winHeight - imageSize - fieldHeight - navHeight - 50),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Help_Text",class_id = "@Button_Bar"),container = helpPanel,html_text = text)
    CreateUIElement(manager,UIButton,(20,-20),(100,fieldHeight),BOTTOM_LEFT,
                    object_id = ObjectID(object_id = "#Back_Help",class_id = "@Button_Bar"),container = helpPanel,text="Back")
    CreateUIElement(manager,UILabel,(winWidth/2-50,-20),(100,fieldHeight),BOTTOM_LEFT,
                    object_id = ObjectID(object_id = "#Help_Page"),container = helpPanel,text = f"Page # 1/{len(helpInfo['explanation'])}")
    CreateUIElement(manager,UIButton,(-20,-20),(100,fieldHeight),BOTTOM_RIGHT,
                    object_id = ObjectID(object_id = "#Next_Help",class_id = "@Button_Bar"),container = helpPanel,text="Next")

# Create all sections of the main UI window
def CreateMainWindow(manager,winWidth = 400,winHeight = 600,navHeight = 50,fieldHeight=40,algorithms = ["A* Algorithm","Dijkstra's Algorithm"],visible = True):
    # The panel that represents the main window
    mainWindow = CreateUIElement(manager,UIPanel,(-20,75),(winWidth,winHeight),TOP_RIGHT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Main_Window"),visible = visible)
    # Load All UI Sections in the Main Window
    baseArgs = [manager,mainWindow,winWidth,winHeight,navHeight,fieldHeight]
    CreateNavigationBar(*baseArgs)
    CreateProperties(*baseArgs,visible = 2)
    CreateFileOptions(*baseArgs)
    CreateHelp(*baseArgs)
    CreateSPProperties(*baseArgs,algorithms)

# ~~~ TOOLBAR UI PANEL ~~~

# Create the toolbar widgets (This is customisable so that there can be different toolbars for different states that can be switched between)
# For example, one may be for editing while one is used simply for viewing graphs and so has limited functionaility.
def Toolbar(manager,name = "#Toolbar",buttonSize = 60,buttons = [],visible = True):
    #The size of the toolbar will be determined by the number of widgets it contains
    toolbar = CreateUIElement(manager,UIPanel,(20,75),(buttonSize,buttonSize * len(buttons)),TOP_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = name,class_id="@Button_Bar"),visible=visible)
    #Create a button with a unique object_id so that it can be distinguished from others and displayed correctly by theme.json
    for i in range(len(buttons)):
        CreateUIElement(manager,UIButton,(0,buttonSize*i),[buttonSize]*2,TOP_LEFT,
                        object_id = ObjectID(object_id = buttons[i],class_id = "@Button_Bar"),container = toolbar,text="")

# ~~~ Algorithm Explanation Panel ~~~

#This UI will be used to explain how the shortest path finding algorithms work.
def AlgorithmExplanation(manager,winWidth = 850,winHeight = 250,widgetSize = 50,visible = False):
    #Explanation text will update depending on which step the user is on.
    explanationWindow = CreateUIElement(manager,UIPanel,(20,-20),(winWidth,winHeight),BOTTOM_LEFT,
                    starting_height = 1, object_id = ObjectID(object_id = "#Explantion_Window"),visible = visible)
    CreateUIElement(manager,UITextBox,(15,widgetSize+15),(winWidth-30,winHeight-widgetSize-30),TOP_LEFT,
                    object_id = ObjectID(object_id = "#Algorithm_Text",class_id = "@Button_Bar"),container = explanationWindow,html_text = "")
    #This UI will allow the user to see their current step and move between them
    CreateUIElement(manager,UILabel,(winWidth / 2 - widgetSize * 2,0),(widgetSize*4,widgetSize),TOP_LEFT,
                        object_id = ObjectID(object_id = "#Step_Number"),container = explanationWindow,text="Step 999 of 1000")
    CreateUIElement(manager,UIButton,(winWidth / 2 + widgetSize * 2,0),(widgetSize*2,widgetSize),TOP_LEFT,
                        object_id = ObjectID(object_id = "#Step_Forward"),container = explanationWindow,text="Next")
    CreateUIElement(manager,UIButton,(winWidth / 2 - widgetSize * 4,0),(widgetSize*2,widgetSize),TOP_LEFT,
                        object_id = ObjectID(object_id = "#Step_Backward"),container = explanationWindow,text="Back")
    CreateUIElement(manager,UIButton,(winWidth / 2 + widgetSize * 4,0),(widgetSize*2,widgetSize),TOP_LEFT,
                        object_id = ObjectID(object_id = "#Skip_Forward"),container = explanationWindow,text="Skip")
    CreateUIElement(manager,UIButton,(winWidth / 2 - widgetSize * 6,0),(widgetSize*2,widgetSize),TOP_LEFT,
                        object_id = ObjectID(object_id = "#Skip_Backward"),container = explanationWindow,text="Restart")
    CreateUIElement(manager,UIButton,(0,0),(widgetSize*2,widgetSize),TOP_RIGHT,
                        object_id = ObjectID(object_id = "#Algorithm_Quit"),container = explanationWindow,text="Quit")

# ~~~ TEMPORARY UI ~~~
# This includes UI which can be created/destroyed as needed

# A function to create label overlays on graphs
def CreateLabel(manager,container,position,objectId,height=30,width= None,anchor = TOP_LEFT,text = ""):
    # Set an arbitrarty size for the label as it will be overwritten each frame to fit the text
    lines = text.split("<br>")
    if not width:
        lines = sorted(lines,key = len)
        size = Vector2(8 * (len(lines[-1]))+20,height)
    else:
        size = Vector2(width,height)
    # A label will consist of a background panel and a piece of text rendered on top of it.
    # The background ensures the text is always easy to read.
    background = CreateUIElement(manager,UIPanel,position,size,anchor,
                    starting_height = 1, container = container,object_id = ObjectID(object_id = objectId, class_id = "@Label"))
    text = CreateUIElement(manager,UITextBox,(0,0),size,anchor,
                    container = background,object_id = ObjectID(object_id = "#Label_Text", class_id = "@Label"),html_text = text)
    return background

# A function which will create a window which prompts the user to do something
# E.g. Asking if they want to save a file before quitting
def Prompt(sharedMemory,manager,title,text,id="#Prompt",size = Vector2(300,200),actionButton = "Ok"):
    pos = sharedMemory["ScreenSize"] / 2
    pos -= size / 2
    
    # Create a dialogue box in the centre of the screen
    UIConfirmationDialog(pygame.Rect(pos.x,pos.y,size.x,size.y),manager = manager,action_long_desc = text,action_short_name=actionButton,object_id = ObjectID(id),window_title = title)

# ~~~ UI GENERATION ~~~

# Create all UI and return the screen surface and pygame_gui manager
def GenerateUI(screenSize):
    pygame.display.set_caption("SP Algorithm Visualiser")
    
    # The UIManager object will be used as a container of all UI features and will be responsible
    # for updating and displaying them to the screen
    # Retrieves JSON data about how UI elements should be displayed - for design testing, this will update live

    # Create the screen surface which will will be painted to display UI and graphs
    
    screen = pygame.display.set_mode((int(screenSize.x),int(screenSize.y)),pygame.RESIZABLE)

    mainUIManager = pygame_gui.UIManager(screenSize,"theme.json",True)

    # All UI panels will be created here. For simplicity of design, the UI shall be designed to run in 1080p fullscreen.
    CreateMainWindow(mainUIManager)
    # Editing toolbar
    Toolbar(mainUIManager,buttons = ["#Select","#Move_Camera","#Create","#Delete","#Zoom_In","#Zoom_Out","#Undo","#Redo","#Home"])
    # Viewing toolbar (used when visualising pathfinding algorithms)
    Toolbar(mainUIManager,buttons = ["#Select","#Move_Camera","#Zoom_In","#Zoom_Out","#Home"],visible = False,name = "#Read_Only_Toolbar")
    
    AlgorithmExplanation(mainUIManager)

    # Another UI manager will also be created for labels associated with graphs
    envUIManager = pygame_gui.UIManager(screenSize,"theme.json",True)

    # Each panel will act as containers for all labels for edges and nodes
    CreateUIElement(envUIManager,UIContainer,(0,0),screenSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Node_UI"))
    CreateUIElement(envUIManager,UIContainer,(0,0),screenSize,TOP_LEFT,
                    object_id = ObjectID(object_id = "#Edge_UI"))

    #Shows the FPS for performance testing
    FPS = CreateLabel(mainUIManager,mainUIManager.get_root_container(),(0,0),"#FPS",30, 100,TOP_RIGHT,"FPS: 0")

    return screen,mainUIManager,envUIManager