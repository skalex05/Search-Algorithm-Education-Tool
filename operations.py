# A set of classes responsible for performing "operations"
# These are actions that can be undone/redone

from functions import NodeFromID, EdgeFromID, UpdatePropertiesUI, UpdateSelection
from graph import Node, Edge

# This is the base class for the operations to prevent repetition of initialisation code.
class Operation:
    def __init__(self,sharedMemory,toStack=True,**kwargs):
        self.arguments = kwargs
        #Clear the redo stack and add this operation to the undo stack if required
        if toStack:
            sharedMemory["RedoStack"] = []
            sharedMemory["UndoStack"].append(self)
            self.Forward(sharedMemory)

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
        if object in sharedMemory["Selected"]:
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
        if object in sharedMemory["Selected"]:
            UpdatePropertiesUI(sharedMemory)

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

#This function creates an appropriate delete operation depending on what type of object is being deleted.
def Delete(object,sharedMemory):
    if type(object) == Node:
        DeleteNodeOperation(sharedMemory,node = object)
    elif type(object) == Edge:
        DeleteEdgeOperation(sharedMemory,edge = object)
    else:
        raise ValueError("Delete function can only be used to delete objects of type Node and Edge")