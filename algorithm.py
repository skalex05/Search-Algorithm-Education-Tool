# A file to contain all code relating to algorithms the program can visualise to the user.

from operations import ChangeProperty
from functions import GetElement, NodeFromID
import math

# This will be used to represent a step in an algorithm visualisation
class Step:
    def __init__(self,explanation,tempOps,permOps):
        self.explanation = explanation # The text explanation for what's happening in the step
        self.tempOps = tempOps # An array of operations which are applied for this single step
        self.permOps = permOps # An array of operations which are applied for all future steps
    def __repr__(self):
        return self.explanation

# A step which will explain why there is no route in SPAs
class NoRoute(Step):
    def __init__(self,startNode,endNode):
        # This step only contains an explanation and does not change the graph.
        super().__init__(f"All possible routes have been considered from {startNode}. However, none of them are able to reach {endNode}. Therefore, there is no path between the two.", [],[])

# ~~~ DIJKSTRA ALGORITHM ~~~
# A list of classes and a function used to generate a set of steps for a Dijkstra's Pathfinding Algorithm


# A step which will contain data to explain and visualise when a new node has been selected
class NodeSelectDijkstra(Step):
    def __init__(self, node,sharedMemory):
        explanation = f"The algorithm looks at all unexplored nodes and selects {node.name} because it has the lowest cost of {node.cost}. This means this is the lowest cost possible to reach this node and so can be explored and marked green."
        tempOps = [ChangeProperty(sharedMemory,False,object = node,attr = "selected", value = True) # Select the node of interest     
        ]
        if node.GetEdgeTo(node.fromN):
            # Select the edge where the lowest cost came from     
            tempOps.append(ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN),attr = "outlineColour", value = sharedMemory["SelectionColour"]))

        # Make the node green indicating it has been explored
        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = "#3ab733")] 
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
        permOps = [ChangeProperty(sharedMemory,False,object = edge,attr = "outlineColour", value = sharedMemory["SelectionColour"]), 
        ChangeProperty(sharedMemory,False,object = node.fromN,attr = "outlineColour", value = sharedMemory["SelectionColour"]),
        ChangeProperty(sharedMemory,False,object = node,attr = "outlineColour", value = sharedMemory["SelectionColour"])
        ] 
        super().__init__(explanation, [], permOps)

# A step which will explain the first step in the A* algorithm
class StartStepDijkstra(Step):
    def __init__(self,startNode,sharedMemory):
        permOps = [ChangeProperty(sharedMemory,False,object = startNode, attr = "colour", value = "#3ab733"),
        ChangeProperty(sharedMemory,False,object = startNode, attr = "cost",old = math.inf,value = 0)
        ]

        super().__init__(f"The program starts at {startNode} and marks it in green.", [],permOps)

# A step which states the final shortest route
class StateRouteDijkstra(Step):
    def __init__(self,startNode,endNode,route):
        # This step only contains an explanation and does not change the graph.
        super().__init__(f"The shortest path between {startNode} and {endNode} has now been calculated with a total cost of {endNode.cost} along the path:<br>{' --> '.join([repr(n) for n in route])}", [],[])

# This algorithm uses the afformentioned classes to create a set of steps for Dijkstra's
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


# ~~~ A* PATHFINDING  ALGORITHM ~~~
# A list of classes and a function used to generate a set of steps for an A* Pathfinding Algorithm


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
            tempOps.append(ChangeProperty(sharedMemory,False,object = node.GetEdgeTo(node.fromN),attr = "outlineColour", value = sharedMemory["SelectionColour"]))

        permOps = [ChangeProperty(sharedMemory,False,object = node, attr = "colour", value = "#3ab733"),] # Make the node green indicating it has been explored
        super().__init__(explanation, tempOps, permOps)

# A step which will backtrack an edge to work out the shortest route
class BacktrackAStar(Step):
    def __init__(self,node,sharedMemory):
        edge = node.GetEdgeTo(node.fromN)
        explanation = f"By inspecting the graph, {node} must have come from {node.fromN} because the weighted cost of {node}, {node.wCost} subtract the weight of {edge}, {edge.weight} is equal to the weighted cost of {node.fromN}, {node.fromN.wCost}"
        # Select the nodes and edges
        permOps = [ChangeProperty(sharedMemory,False,object = edge,attr = "outlineColour", value = sharedMemory["SelectionColour"]), 
        ChangeProperty(sharedMemory,False,object = node.fromN,attr = "outlineColour", value = sharedMemory["SelectionColour"]),
        ChangeProperty(sharedMemory,False,object = node,attr = "outlineColour", value = sharedMemory["SelectionColour"])
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

# Creates a list of steps for A* 
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
            # Add a step for each step in the backtrack process
            steps.append(BacktrackAStar(route[-1],sharedMemory))
            route.append(route[-1].fromN)
        steps.append(BacktrackAStar(route[-1],sharedMemory))
        route = [startNode]+route[::-1]
        steps.append(StateRouteAStar(startNode,endNode,route))
    sharedMemory["Step"] = 0
    sharedMemory["Steps"] = steps