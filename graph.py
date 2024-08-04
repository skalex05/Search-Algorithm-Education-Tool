# This file contains code about creating graphs

from functions import NameNode, GetElement, EnvToScn, NodeFromID, NewEnv, NodeFromID,UpdateSelection
from gui import CreateLabel
import pygame
from pygame.math import Vector2
from pygame import Color
from pygame import gfxdraw
import pygame.transform
import math
import random
import tkinter
from tkinter import filedialog
import os
import pickle

# ~~~ GRAPH CLASSES ~~~

# A datastructure used to represent a node
class Node:
    def __init__(self,sharedMemory,position,name = None,colour = None,outColour = None,radius = 50,id = None):
        if colour == None:
            colour = sharedMemory["Defaults"]["NodeColour"]
        if type(name) != str: # Create a default node name
            name = NameNode(sharedMemory)
        # Create a label which will display the name of this node
        self.type = "Node"
        
        # Assign a unique number to each node so they can be individually identified
        if id == None:
            id = sharedMemory["NodeCount"]
            sharedMemory["NodeCount"] += 1
        self.id = id

        # Create variables associated with the class
        self.name = name
        self.colour = colour
        self.outlineColour = outColour
        self.position = position
        self.velocity = Vector2(0,0)
        self.radius = radius
        self.connectedEdges = []
        self.connectedNodes = []
        self.selected = False
        sharedMemory["Nodes"].append(self) # Add the node to a list of nodes which can be accessed through shared memory

        # Create a label
        self.UpdateLabel(sharedMemory,False)
    # Appropriately removes a node from a graph
    def Destroy(self,sharedMemory):
        #Delete the UI label
        self.UILabel.kill()
        sharedMemory["Nodes"].remove(self)
        # Delete all edges connected to this node
        while len(self.connectedEdges):
            self.connectedEdges[0].Destroy(sharedMemory)
    def GetEdgeTo(self,node):
        for edge in self.connectedEdges:
            if edge.nodeA == node or edge.nodeB == node:
                return edge
        return None
    def DragToward(self,position,sharedMemory):
        # Manual adjustment to the positon of a node
        # Works with the same forces as for the automatic adjustment for smoother results
        offset = (position - self.position)
        # Calculate the direction and distance so that the resultant force can be calculated
        direction = offset.normalize()
        distance = offset.magnitude()
        maxForce = sharedMemory["MaxForce"]
        slope = sharedMemory["AdjustmentRate"]
        force = 20 * maxForce * math.tanh(((distance)**3) / (slope**3))
        # Apply resultant velocity
        self.velocity = force * direction
    def Draw(self,screen,sharedMemory):
        # Draw a circle representing each node onto the screen
        pos = EnvToScn(self.position,sharedMemory)
        #Draw an outline around the circle where applicable
        outColour = self.outlineColour
        if self.selected:
            outColour = sharedMemory["SelectionColour"]
        if outColour:
            gfxdraw.filled_circle(screen, int(pos.x), int(pos.y), int((self.radius+5)*(sharedMemory["Scale"])), Color(outColour))
            gfxdraw.aacircle(screen, int(pos.x), int(pos.y), int((self.radius+5)*(sharedMemory["Scale"])), Color(outColour))
        gfxdraw.aacircle(screen, int(pos.x), int(pos.y), int((self.radius)*(sharedMemory["Scale"])), Color(self.colour))
        gfxdraw.filled_circle(screen, int(pos.x), int(pos.y), int((self.radius)*(sharedMemory["Scale"])), Color(self.colour))
    def UpdateLabel(self,sharedMemory,delete = True):
        #Create a new label for this edge
        self.manager = sharedMemory["EnvUIManager"]
        nodeUI = GetElement(self.manager.get_root_container(),"#Node_UI") # Get the container where this label will be stored
        
        if sharedMemory["SPA"] == "Dijkstra's Algorithm" and not sharedMemory["Edit"]:
            # Display the cost and name when performing dijkstra's algorithm
            UILabel = CreateLabel(self.manager,nodeUI,(0,0),"Node_Label",height=65,text = f"{self.name}<br>{[str(self.cost),'∞'][self.cost == math.inf]}")
        elif sharedMemory["SPA"] == "A* Algorithm" and not sharedMemory["Edit"]:
            # Display the three cost variables when performing A*
            UILabel = CreateLabel(self.manager,nodeUI,(0,0),"Node_Label",height=65,text = f"{self.name}<br>{[str(self.wCost),'∞'][self.wCost == math.inf]}, {self.hCost}, {[str(self.tCost),'∞'][self.tCost == math.inf]}")
        else:
            # Just display the name of the node
            UILabel = CreateLabel(self.manager,nodeUI,(0,0),"Node_Label",text = str(self.name))
        if delete:
            self.UILabel.kill()
        self.UILabel = UILabel
    # Compiles all data needed to rebuild this node
    def CompileData(self):
        return (self.position,self.name,self.colour,self.outlineColour,self.radius,self.id)
    # Additional function to aid debugging
    def __repr__(self):
        return self.name

# Another datastructure to represent edges between nodes
class Edge:
    def __init__(self,sharedMemory,nodeA,nodeB, colour = None,outColour = None, name = None, weight = None, length = None, width = 25,id = None):
        #Set defaults
        if colour == None:
            colour = sharedMemory["Defaults"]["EdgeColour"]
        if weight == None:
            weight = sharedMemory["Defaults"]["EdgeWeight"]
        if length == None:
            length = sharedMemory["Defaults"]["EdgeLength"]
        
        if type(name) != str: # Create a default edge name
            name = f"{nodeA.name} -- {nodeB.name}"
        self.type = "Edge"
        if id == None:
            id = sharedMemory["EdgeCount"]
            sharedMemory["EdgeCount"] += 1
        self.id = id
        # Create all variables for an edge
        self.name = name
        self.colour = colour
        self.outlineColour = outColour
        self.nodeA = nodeA
        self.nodeB = nodeB
        self.weight = weight
        self.length = length
        self.width = width
        self.selected = False

        # Create a label which will display the weight of this edge
        self.UpdateLabel(sharedMemory,False)

        # Add this edge to both node's list of connected edges and nodes.
        nodeA.connectedEdges.append(self)
        nodeA.connectedNodes.append(nodeB)
        nodeB.connectedEdges.append(self)
        nodeB.connectedNodes.append(nodeA)
        # Add the node also to an array in shared memory
        sharedMemory["Edges"].append(self)
    def Mid(self):
        return (self.nodeA.position + self.nodeB.position) / 2
    def GetOtherNode(self,node):
        if node == self.nodeA:
            return self.nodeB
        elif node == self.nodeB:
            return self.nodeA
        raise ValueError(f"{node} is not a node in the edge, {self}")
    def Destroy(self,sharedMemory):
        # Delete UI label
        self.UILabel.kill()
        # Remove the edge from all associated lists
        self.nodeA.connectedEdges.remove(self)
        self.nodeA.connectedNodes.remove(self.nodeB)
        self.nodeB.connectedEdges.remove(self)
        self.nodeB.connectedNodes.remove(self.nodeA)
        sharedMemory["Edges"].remove(self)
    def Draw(self,screen,sharedMemory):
        #Calculate the start and end positions of the edge onscreen
        startPos = EnvToScn(self.nodeA.position,sharedMemory)
        endPos =  EnvToScn(self.nodeB.position,sharedMemory)
        # Diplay an optional outline around nodes
        # This will be overwritten if the node is selected
        outColour = self.outlineColour
        if self.selected:
            outColour = sharedMemory["SelectionColour"]
        if outColour:
            pygame.draw.line(screen,outColour,startPos,endPos,width = int((self.width+10) * sharedMemory["Scale"]))
        pygame.draw.line(screen,self.colour,startPos,endPos,width = int(self.width * sharedMemory["Scale"]))
    def UpdateLabel(self,sharedMemory,delete = True):
        #Create a new label for this edge
        self.manager = sharedMemory["EnvUIManager"]
        edgeUI = GetElement(self.manager.get_root_container(),"#Edge_UI") # Get the container where this label will be stored
        UILabel = CreateLabel(self.manager,edgeUI,(0,0),"Edge_Label",text = str(self.weight))
        if delete:
            self.UILabel.kill()
        self.UILabel = UILabel
    # Compiles all data needed to rebuild this edge
    def CompileData(self):
        return (self.nodeA.id,self.nodeB.id,self.colour,self.outlineColour,self.name,self.weight,self.length,self.width,self.id)

    #Additional function for debugging
    def __repr__(self):
        return self.name

# ~~~ FILE FUNCTIONS ~~~
# These functions are resposible for saving and loading graphs from files
# They are seperate as they require direct reference to Node/Edge classes

# Save/Load functions are here as they have Node/Edge dependencies
def Save(sharedMemory,askdir = True):
    # Ensure the user can't make changes to the graph while saving
    sharedMemory["SelectedTool"] = "#Move_Camera"
    # If a directory must be chosen, the following condition is run
    if askdir or sharedMemory["SaveDir"] == None:
        # Create an empty tkinter instance
        root = tkinter.Tk()
        root.withdraw()
        # Create a file dialogue and store the path returned
        file = filedialog.asksaveasfilename(filetypes = [("Graph files","*.grav")],initialdir = os.getcwd(),defaultextension = "*.grav")
        root.destroy()
        # If an invalid
        if file == "" or not file.endswith(".grav"):
            return
        sharedMemory["SaveDir"] = file
    else:
        file = sharedMemory["SaveDir"]

    nodeData = []
    # Add data about each node to an array
    for node in sharedMemory["Nodes"]:
        nodeData.append(node.CompileData())
    edgeData = []
    # Add data about each edge to an array
    for edge in sharedMemory["Edges"]:
        edgeData.append(edge.CompileData())

    # If a valid path was entered, pickle the nodes and edges into a file
    pickle.dump((nodeData,edgeData,sharedMemory["NodeCount"],sharedMemory["EdgeCount"]),open(file,"wb"))
    sharedMemory["Changed"] = False

def Open(sharedMemory):
    # Ensure the user can't make changes to the graph while saving
    sharedMemory["SelectedTool"] = "#Move_Camera"
    # Get the user to choose what file to open
    root = tkinter.Tk()
    root.withdraw()
    # Create a file dialogue and store the path returned
    file = filedialog.askopenfilename(filetypes = [("Graph files","*.grav")],initialdir = os.getcwd(),defaultextension = "*.grav")
    root.destroy()
    # If an invalid path is given
    if file == "" or not file.endswith(".grav"):
        # Abort successfully
        return True
    
    # Unload data
    data = None
    try:
        data = pickle.load(open(file,"rb"))
    except Exception:
        # If the file could not be opened return False
        return False

    #Reset the environment for the new graph
    NewEnv(sharedMemory)
    nodeData,edgeData, sharedMemory["NodeCount"], sharedMemory["EdgeCount"] = data
    # Rebuild nodes from their data
    for node in nodeData:
        Node(sharedMemory,*node)
    # Rebuild edges from their data
    for edge in edgeData:
        # Get the nodes from their ids
        nodeA = NodeFromID(edge[0],sharedMemory)
        nodeB = NodeFromID(edge[1],sharedMemory)
        Edge(sharedMemory,nodeA,nodeB,*edge[2::])
    # Set the save directory to this file
    sharedMemory["SaveDir"] = file
    return True

# ~~~ TEST FUNCTIONS ~~~

def GenerateGraph(sharedMemory,nodeCount,edgeCount):
    if nodeCount < 2:
        print("Node count must be >= 2")
        return
    nodes = []
    for i in range(nodeCount):
        nodes.append(Node(sharedMemory,Vector2(0,0)))
    i = 0
    while i < edgeCount:
        n1 = random.randint(0,nodeCount-1)
        n2 = random.randint(0,nodeCount-1)
        if n1 != n2 and nodes[n1] not in nodes[n2].connectedNodes:
            i += 1
            Edge(sharedMemory,nodes[n1],nodes[n2],weight=random.randint(5,30))
            
def GenerateKGraph(sharedMemory,n):
    for i in range(n):
        Node(sharedMemory,Vector2(0,0))
    for n1 in sharedMemory["Nodes"]:
        for n2 in sharedMemory["Nodes"]:
            if n1 == n2:
                continue
            Edge(sharedMemory,n1,n2,length = 100)