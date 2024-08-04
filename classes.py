import pygame
from functions import *
from gui import CreateLabel
import string

#A trivial function which will create unique default names for nodes
def NameNode(sharedMemory):
    n = sharedMemory["NodeCount"]
    name = ""
    #Convert the node count into a alphabetical name
    while n > 0:
        name = string.ascii_uppercase[n % 26 - 1] + name
        n //= 27
    return name

class Node:
    def __init__(self,sharedMemory,position,name = None,colour = "#e52929",outColour = None,radius = 50,id = None):
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
        if sharedMemory["Selected"] == self:
            UpdateSelection(sharedMemory,None)
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
            outColour = "#00d0f9"
        if outColour:
            pygame.draw.circle(screen,outColour,pos,(self.radius+5)*(sharedMemory["Scale"]))
        pygame.draw.circle(screen,self.colour,pos,self.radius*(sharedMemory["Scale"]))
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

class Edge:
    def __init__(self,sharedMemory,nodeA,nodeB, colour = "#5e6060",outColour = None, name = None, weight = 10, length = 10, width = 25,id = None):
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
        if sharedMemory["Selected"] == self:
            UpdateSelection(sharedMemory,None)
    def Draw(self,screen,sharedMemory):
        #Calculate the start and end positions of the edge onscreen
        startPos = EnvToScn(self.nodeA.position,sharedMemory)
        endPos =  EnvToScn(self.nodeB.position,sharedMemory)
        # Diplay an optional outline around nodes
        # This will be overwritten if the node is selected
        outColour = self.outlineColour
        if self.selected:
            outColour = "#00d0f9"
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

#This function creates an appropriate delete operation depending on what type of object is being deleted.
def Delete(object,sharedMemory):
    UpdateSelection(sharedMemory,None)
    if type(object) == Node:
        DeleteNodeOperation(sharedMemory,node = object)
    elif type(object) == Edge:
        DeleteEdgeOperation(sharedMemory,edge = object)
    else:
        raise ValueError("Delete function can only be used to delete objects of type Node and Edge")
        
# This is the base class for the operations to prevent repetition of initialisation code.
class Operation:
    def __init__(self,sharedMemory,toStack=True,**kwargs):
        self.arguments = kwargs
        #Clear the redo stack and add this operation to the undo stack if required
        if toStack:
            sharedMemory["RedoStack"] = []
            sharedMemory["UndoStack"].append(self)
            self.Forward(sharedMemory)

# This class represents an operation which creates a new node
class CreateNodeOperation(Operation):
    def Forward(self,sharedMemory):
        self.node = Node(sharedMemory,**self.arguments)  #Create a node from the supplied keyword arguments
        #Record all important variables to the arguments dictionary
        self.arguments["id"] = self.node.id 
        self.arguments["name"] = self.node.name
        self.arguments["colour"] = self.node.colour
        self.arguments["outColour"] = self.node.outlineColour
        self.arguments["radius"] = self.node.radius
    def Backward(self,sharedMemory):
        #Find a node which corresponds to the unique ID and destroys it
        NodeFromID(self.arguments["id"],sharedMemory).Destroy(sharedMemory) 

# This class represents an operation for creating a new edge
class CreateEdgeOperation(Operation):
    def Forward(self,sharedMemory):
        if type(self.arguments["nodeA"]) == int:
            self.arguments["nodeA"] = NodeFromID(self.arguments["nodeA"],sharedMemory)
            self.arguments["nodeB"] = NodeFromID(self.arguments["nodeB"],sharedMemory)
        self.edge = Edge(sharedMemory,**self.arguments)  #Create an edge from the supplied keyword arguments
        #Record all important variables to the arguments dictionary
        self.arguments["id"] = self.edge.id
        self.arguments["nodeA"] = self.edge.nodeA.id
        self.arguments["nodeB"] = self.edge.nodeB.id
        self.arguments["name"] = self.edge.name
        self.arguments["colour"] = self.edge.colour
        self.arguments["outColour"] = self.edge.outlineColour
        self.arguments["width"] = self.edge.width
        self.arguments["weight"] = self.edge.weight
        self.arguments["length"] = self.edge.length
    def Backward(self,sharedMemory):
        #Find an edge which corresponds to the unique ID and destroys it
        EdgeFromID(self.arguments["id"],sharedMemory).Destroy(sharedMemory)

# This class represents an operation for deleting an edge
class DeleteEdgeOperation(Operation):
    def Forward(self,sharedMemory):
        if "edge" in self.arguments:
            edge = self.arguments["edge"]
            #Record all important variables to the arguments dictionary
            self.arguments.pop("edge")
            self.arguments["id"] = edge.id
            self.arguments["nodeA"] = edge.nodeA.id
            self.arguments["nodeB"] = edge.nodeB.id
            self.arguments["name"] = edge.name
            self.arguments["colour"] = edge.colour
            self.arguments["outColour"] = edge.outlineColour
            self.arguments["width"] = edge.width
            self.arguments["weight"] = edge.weight
            self.arguments["length"] = edge.length
        else:
            #If forward is called more than once, data retrieval can be skipped
            edge = EdgeFromID(self.arguments["id"],sharedMemory)
        edge.Destroy(sharedMemory) 
    def Backward(self,sharedMemory):
        #Find an edge which corresponds to the unique ID and destroys it
        self.arguments["nodeA"] = NodeFromID(self.arguments["nodeA"],sharedMemory)
        self.arguments["nodeB"] = NodeFromID(self.arguments["nodeB"],sharedMemory)
        edge = Edge(sharedMemory,**self.arguments)  #Create an edge from the supplied keyword arguments
        self.arguments["nodeA"] = edge.nodeA.id
        self.arguments["nodeB"] = edge.nodeB.id

# This class represents an operation for deleting a node
class DeleteNodeOperation(Operation):
    def Forward(self,sharedMemory):
        if "node" in self.arguments:
            node = self.arguments["node"]
            #Record all important variables to the arguments dictionary
            self.arguments.pop("node")
            self.arguments["id"] = node.id 
            self.arguments["position"] = node.position
            self.arguments["name"] = node.name
            self.arguments["colour"] = node.colour
            self.arguments["outColour"] = node.outlineColour
            self.arguments["radius"] = node.radius
            self.edgeOps = []
            # Create an operation for each connected edge which is deleted
            while len(node.connectedEdges):
                # This edge operation is not added to the stack
                edgeOp = DeleteEdgeOperation(sharedMemory,toStack = False,edge=node.connectedEdges[0])
                # The forward function must be called seperately to delete the edge and store edge data
                edgeOp.Forward(sharedMemory)
                self.edgeOps.append(edgeOp)
            node.Destroy(sharedMemory) 
        else:
            # Data doesnt need to be re-retrieved if this function has already been run
            node = NodeFromID(self.arguments["id"],sharedMemory)
            node.Destroy(sharedMemory) 
    def Backward(self,sharedMemory):
        Node(sharedMemory,**self.arguments)
        #Recreate each edge, connected to the node, which was deleted
        for edgeOp in self.edgeOps:
            edgeOp.Backward(sharedMemory)

# This class will be used by the properties panel to apply changes to the graph
# It will also be a fundamental component for visualising SP algorithms
class ChangeProperty(Operation):
    def Forward(self,sharedMemory):
        # First-time forward function
        if "object" in self.arguments:
            # Get the old value
            object = self.arguments["object"]
            if "old" not in self.arguments:
                # Only set the original value if not already specified on init
                self.arguments["old"] = getattr(object,self.arguments["attr"])
            # Record the type of object (node/edge) and its id so it can be retrieved later
            self.arguments["type"] = object.type
            self.arguments["id"] = object.id
            # Remove the object key
            self.arguments.pop("object")
        # Executing forward function again will use the type and id keys
        elif self.arguments["type"] == "Node":
            object = NodeFromID(self.arguments["id"],sharedMemory)
        elif self.arguments["type"] == "Edge":
            object = EdgeFromID(self.arguments["id"],sharedMemory)

        # Update the value
        setattr(object,self.arguments["attr"],self.arguments["value"])
        # Update UI values where appropriate
        if self.arguments["attr"] in ["weight","name","cost","wCost","hCost","tCost"]:
            object.UpdateLabel(sharedMemory)
        if sharedMemory["Selected"] == object:
            UpdatePropertiesUI(sharedMemory)
    def Backward(self,sharedMemory):
        # Get the most recent instance of the associated object
        if self.arguments["type"] == "Node":
            object = NodeFromID(self.arguments["id"],sharedMemory)
        elif self.arguments["type"] == "Edge":
            object = EdgeFromID(self.arguments["id"],sharedMemory)
        
        # Update the value to its original value
        setattr(object,self.arguments["attr"],self.arguments["old"])
        if self.arguments["attr"] in ["weight","name","cost","wCost","hCost","tCost"]:
            object.UpdateLabel(sharedMemory)
        if sharedMemory["Selected"] == object:
            UpdatePropertiesUI(sharedMemory)

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
        file = tkinter.filedialog.asksaveasfilename(filetypes = [("Graph files","*.grav")],initialdir = os.getcwd(),defaultextension = "*.grav")
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
    file = tkinter.filedialog.askopenfilename(filetypes = [("Graph files","*.grav")],initialdir = os.getcwd(),defaultextension = "*.grav")
    root.destroy()
    # If an invalid path is given
    if file == "" or not file.endswith(".grav"):
        return
    #Reset the environment for the new graph
    NewEnv(sharedMemory)
    # Unload data
    nodeData,edgeData, sharedMemory["NodeCount"], sharedMemory["EdgeCount"] = pickle.load(open(file,"rb"))
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

# This will be used to represent the steps carried out by SPAs
class Step:
    def __init__(self,explanation,tempOps,permOps):
        self.explanation = explanation # The text explanation for what's happening in the step
        self.tempOps = tempOps # An array of operations which are applied for this single step
        self.permOps = permOps # An array of operations which are applied for all future steps
    def __repr__(self):
        return self.explanation

# A step which will contain data to explain and visualise when a new node has been selected
class NodeSelectDijkstra(Step):
    def __init__(self, node,sharedMemory):
        explanation = f"The algorithm looks at all unexplored nodes and selects {node.name} because it has the lowest cost of {node.cost}. This means this is the lowest cost possible to reach this node and so can be explored and marked green."
        tempOps = [ChangeProperty(sharedMemory,False,object = node,attr = "selected", value = True) # Select the node of interest     
        ]
        if node.GetEdgeTo(node.fromN):
            # Select the edge where the lowest cost came from     
            tempOps.append(ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN),attr = "selected", value = True))

        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = "#3ab733"),] # Make the node green indicating it has been explored
        super().__init__(explanation, tempOps, permOps)

# A step which will explain when and where a new cost has been calculated for dijkstras
class NodeCostDijkstra(Step):
    def __init__(self, node, previousNode,oldCost,newCost,sharedMemory):
        edge = node.GetEdgeTo(previousNode)
        # Have a different explanation depending on if this is the first time the cost has been calculated
        if node.cost == math.inf:
            explanation = f"The algorithm considers {node} and marks it in yellow. To calculate the cost to reach this node it takes the cost of {previousNode} which is {previousNode.cost} and adds the weight of {edge} which is {edge.weight}. Therefore, the cost of {node} is {previousNode.cost}+{edge.weight} = {newCost}"
        else:
            explanation = f"A shorter route has been found to reach {node} through {previousNode}. The new cost is therefore, {previousNode.cost} + {edge.weight} = {newCost}"
        tempOps = [ChangeProperty(sharedMemory,False,object = node, attr = "selected", value = True), # Select the node of interest
        ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN), attr = "selected", value = True) # Select the edge where the lowest cost came from
        ]             
            
        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = "#e0b818"), # Make the node yellow indicating it has been added to the unexplored
        ChangeProperty(sharedMemory,False,object = node, attr = "cost",old = oldCost,value = newCost)] # Update the cost of a node
        super().__init__(explanation, tempOps, permOps)

# A step which will backtrack an edge to work out the shortest route
class BacktrackDijkstra(Step):
    def __init__(self,node,sharedMemory):
        edge = node.GetEdgeTo(node.fromN)
        explanation = f"By inspecting the graph, {node} must have come from {node.fromN} because the cost of {node}, {node.cost} subtract the weight of {edge}, {edge.weight} is equal to the cost of {node.fromN}, {node.fromN.cost}"
        # Select the nodes and edges
        permOps = [ChangeProperty(sharedMemory,False,object = edge, attr = "selected", value = True), 
        ChangeProperty(sharedMemory,False,object = node.fromN, attr = "selected", value = True),
        ChangeProperty(sharedMemory,False,object = node, attr = "selected", value = True)
        ] 
        super().__init__(explanation, [], permOps)

# A step which will explain the first step in the A* algorithm
class StartStepDijkstra(Step):
    def __init__(self,startNode,sharedMemory):
        permOps = [ChangeProperty(sharedMemory,False,object = startNode, attr = "colour", value = "#3ab733"),
        ChangeProperty(sharedMemory,False,object = startNode, attr = "cost",old = math.inf,value = 0)
        ]

        super().__init__(f"The program starts at {startNode} and marks it in green.", [],permOps)

# A step which will explain why there is no route
class NoRoute(Step):
    def __init__(self,startNode,endNode):
        # This step only contains an explanation and does not change the graph.
        super().__init__(f"All possible routes have been considered from {startNode}. However, none of them are able to reach {endNode}. Therefore, there is no path between the two.", [],[])

# A step which states the final shortest route
class StateRouteDijkstra(Step):
    def __init__(self,startNode,endNode,route):
        # This step only contains an explanation and does not change the graph.
        super().__init__(f"The shortest path between {startNode} and {endNode} has now been calculated with a total cost of {endNode.cost} along the path:<br>{' --> '.join([repr(n) for n in route])}", [],[])

class NodeCostAStar(Step):
    def __init__(self, node, previousNode,oldCost,newCost,sharedMemory):
        edge = node.GetEdgeTo(previousNode)
        # Have a different explanation depending on if this is the first time the cost has been calculated
        if node.wCost == math.inf:
            explanation = f"The algorithm considers {node} and marks it in yellow. To calculate the weighted cost to reach this node it takes the weighted cost of {previousNode} which is {previousNode.wCost} and adds the weight of {edge} which is {edge.weight}. Therefore, the weighted cost of {node} is {previousNode.wCost}+{edge.weight} = {newCost}. This weighted cost can be added to the heuristic cost of {node}, {node.hCost} to calculate the total cost of the node which is {node.hCost + newCost}"
        else:
            explanation = f"A shorter route has been found to reach {node} through {previousNode}. The new cost is therefore, {previousNode.wCost} + {edge.weight} = {newCost}"
        tempOps = [ChangeProperty(sharedMemory,False,object = node, attr = "selected", value = True), # Select the node of interest
        ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN), attr = "selected", value = True) # Select the edge where the lowest cost came from
        ]             
            
        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = ["#e0b818","#3ab733"][node.explored]), # Make the node yellow indicating it has been added to the unexplored
        ChangeProperty(sharedMemory,False,object = node, attr = "wCost",old = oldCost,value = newCost), # Update the weighted cost of a node
        ChangeProperty(sharedMemory,False,object = node, attr = "tCost",old = oldCost + node.hCost,value = newCost + node.hCost) # Update the total cost of a node
        ] 
        super().__init__(explanation, tempOps, permOps)

# A step which will contain data to explain and visualise when a new node has been selected
class NodeSelectAStar(Step):
    def __init__(self, node,sharedMemory):
        explanation = f"The algorithm looks at all unexplored nodes and selects {node.name} because it has the lowest total cost of {node.tCost}. This means this is the lowest cost possible to reach this node and so can be explored and marked green."
        tempOps = [ChangeProperty(sharedMemory,False,object = node,attr = "selected", value = True) # Select the node of interest     
        ]
        if node.GetEdgeTo(node.fromN):
            # Select the edge where the lowest cost came from     
            tempOps.append(ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN),attr = "selected", value = True))

        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = "#3ab733"),] # Make the node green indicating it has been explored
        super().__init__(explanation, tempOps, permOps)

# A step which will backtrack an edge to work out the shortest route
class BacktrackAStar(Step):
    def __init__(self,node,sharedMemory):
        edge = node.GetEdgeTo(node.fromN)
        explanation = f"By inspecting the graph, {node} must have come from {node.fromN} because the weighted cost of {node}, {node.wCost} subtract the weight of {edge}, {edge.weight} is equal to the weighted cost of {node.fromN}, {node.fromN.wCost}"
        # Select the nodes and edges
        permOps = [ChangeProperty(sharedMemory,False,object = edge, attr = "selected", value = True), 
        ChangeProperty(sharedMemory,False,object = node.fromN, attr = "selected", value = True),
        ChangeProperty(sharedMemory,False,object = node, attr = "selected", value = True)
        ] 
        super().__init__(explanation, [], permOps)

# A step which will explain the first step in the A* algorithm
class StartStepAStar(Step):
    def __init__(self,startNode,sharedMemory):
        permOps = [ChangeProperty(sharedMemory,False,object = startNode, attr = "colour", value = "#3ab733"),
        ChangeProperty(sharedMemory,False,object = startNode, attr = "wCost",old = math.inf,value = 0)
        ]

        super().__init__(f"The program starts at {startNode} and marks it in green. The heuristic cost for each node is also calculated. These represent the direct distance from the end node. Therefore, the higher the heuristic cost, the further away the node is.", [],permOps)

# A step which states the final shortest route
class StateRouteAStar(Step):
    def __init__(self,startNode,endNode,route):
        # This step only contains an explanation and does not change the graph.
        super().__init__(f"The shortest path between {startNode} and {endNode} has now been calculated with a total cost of {endNode.tCost} along the path:<br>{' --> '.join([repr(n) for n in route])}", [],[])

# ~~~ Shortest Path Algorithm Functions ~~~
def Dijkstra(sharedMemory,root):
    # Put the program into read-only mode
    sharedMemory["SPA"] = "Dijkstra's Algorithm"
    sharedMemory["SelectedTool"] = "#Move_Camera"
    sharedMemory["Edit"] = False
    GetElement(root,"#Toolbar").hide()
    GetElement(root,"#Read_Only_Toolbar").show()
    GetElement(root,"#Explantion_Window").show()

    # Get the nodes from their ids
    startNode = NodeFromID(sharedMemory["SPAStartNode"],sharedMemory)
    endNode = NodeFromID(sharedMemory["SPAEndNode"],sharedMemory)
    # Set/Reset some variables 
    for node in sharedMemory["Nodes"]:
        node.explored = False
        node.selected = False
        node.cost = math.inf
        node.fromN = None
        node.UpdateLabel(sharedMemory)
    for edge in sharedMemory["Edges"]:
        edge.selected = False
    # Set up to begin searching for the shortest path
    unexplored = [startNode]
    startNode.cost = 0
    endNodeReached = False
    # An array which will store all steps in the algorithm
    steps = [StartStepDijkstra(startNode,sharedMemory)]
    #steps.append(StartStep(startNode,sharedMemory))
    while unexplored != [] and not endNodeReached:
        # Find the node with the lowest cost out of all unexplored nodes
        bestNode = unexplored[0]
        for node in unexplored:
            if node.cost < bestNode.cost:
                bestNode = node
        # Mark the best node as explored
        # The route to this node with the lowest cost has been found
        bestNode.explored = True
        unexplored.remove(bestNode)
        # Add a step each time a node is selected
        if startNode != bestNode:
            steps.append(NodeSelectDijkstra(bestNode,sharedMemory))
        # If the end node has been reached then the algorithm is complete
        if bestNode == endNode:
            endNodeReached = True
            continue
        # Add neighbouring, unexplored nodes and calculate the cost to reach these nodes
        for node in bestNode.connectedNodes:
            if node.explored:
                continue
            # Get the edge between this node and the best node
            edge = node.GetEdgeTo(bestNode)
            # Calculate the cost to reach this node
            cost = bestNode.cost + edge.weight
            # If the cost is a new best, the cost is updated and it is recorded where the route came from
            if cost < node.cost:
                node.fromN = bestNode
                # Add a step each time a new cost is calculated / node is added to unexplored array
                steps.append(NodeCostDijkstra(node,bestNode,node.cost,cost,sharedMemory))
                node.cost = cost
            # Add the node to the unexplored array if not already there
            if node not in unexplored:
                unexplored.append(node)
    if not endNodeReached:
        # Add a step explaining no route could be found
        steps.append(NoRoute(startNode,endNode))
    else:
        route = [endNode]
        # Backtrack from the endNode to find out the shortest path
        while route[-1].fromN != startNode:
            steps.append(BacktrackDijkstra(route[-1],sharedMemory))
            route.append(route[-1].fromN)
            # Add a step for each step in the backtrack process
        steps.append(BacktrackDijkstra(route[-1],sharedMemory))
        route = [startNode]+route[::-1]
        steps.append(StateRouteDijkstra(startNode,endNode,route))
    sharedMemory["Step"] = 0
    sharedMemory["Steps"] = steps

def AStar(sharedMemory,root):
    # Put the program into read-only mode
    sharedMemory["SPA"] = "A* Algorithm"
    sharedMemory["SelectedTool"] = "#Move_Camera"
    sharedMemory["Edit"] = False
    GetElement(root,"#Toolbar").hide()
    GetElement(root,"#Read_Only_Toolbar").show()
    GetElement(root,"#Explantion_Window").show()

    # Get the nodes from their ids
    startNode = NodeFromID(sharedMemory["SPAStartNode"],sharedMemory)
    endNode = NodeFromID(sharedMemory["SPAEndNode"],sharedMemory)
    # Set/Reset some variables 
    for node in sharedMemory["Nodes"]:
        node.explored = False
        node.selected = False
        # Total, weight and heuristic costs are used in this algorithm
        node.tCost = math.inf
        # Heuristic cost is done by finding the direct length between nodes. This value is scaled to fit with other weights
        node.hCost = int((node.position - endNode.position).magnitude() * (sharedMemory["HeuristicMultiplier"]))
        node.wCost = math.inf
        node.fromN = None
        node.UpdateLabel(sharedMemory)
    for edge in sharedMemory["Edges"]:
        edge.selected = False
    # Set up to begin searching for the shortest path
    unexplored = [startNode]
    startNode.wCost = 0
    startNode.tCost = startNode.hCost
    endNodeReached = False
    # An array which will store all steps in the algorithm
    steps = [StartStepAStar(startNode,sharedMemory)]
    #steps.append(StartStep(startNode,sharedMemory))
    while unexplored != [] and not endNodeReached:
        # Find the node with the lowest total cost out of all unexplored nodes
        bestNode = unexplored[0]
        for node in unexplored:
            if node.tCost < bestNode.tCost:
                bestNode = node
        # Mark the best node as explored
        # The route to this node with the lowest cost has been found
        bestNode.explored = True
        unexplored.remove(bestNode)
        # Add a step each time a node is selected
        if startNode != bestNode:
            steps.append(NodeSelectAStar(bestNode,sharedMemory))
        # If the end node has been reached then the algorithm is complete
        if bestNode == endNode:
            endNodeReached = True
            continue
        # Add neighbouring, unexplored nodes and calculate the cost to reach these nodes
        for node in bestNode.connectedNodes:
            # Get the edge between this node and the best node
            edge = node.GetEdgeTo(bestNode)
            # Calculate the cost to reach this node
            wCost = bestNode.wCost + edge.weight
            # If the cost is a new best, the cost is updated and it is recorded where the route came from
            if wCost < node.wCost:
                node.fromN = bestNode
                # Add a step each time a new weighted cost is calculated / node is added to unexplored array
                steps.append(NodeCostAStar(node,bestNode,node.wCost,wCost,sharedMemory))
                node.wCost = wCost
                node.tCost = wCost + node.hCost
            # Add the node to the unexplored array if not already there
            if node not in unexplored and not node.explored:
                unexplored.append(node)
    if not endNodeReached:
        # Add a step explaining no route could be found
        steps.append(NoRoute(startNode,endNode))
    else:
        route = [endNode]
        # Backtrack from the endNode to find out the shortest path
        while route[-1].fromN != startNode:
            steps.append(BacktrackAStar(route[-1],sharedMemory))
            route.append(route[-1].fromN)
            # Add a step for each step in the backtrack process
        steps.append(BacktrackAStar(route[-1],sharedMemory))
        route = [startNode]+route[::-1]
        steps.append(StateRouteAStar(startNode,endNode,route))
    sharedMemory["Step"] = 0
    sharedMemory["Steps"] = steps

# This function is just used for testing and can create a random graph given a number of nodes and edges
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
