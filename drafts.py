import time
import torch
from rubik54 import Cube, Move
from utils.cube_model import ResnetModel
from collections import OrderedDict
import re
from utils.search_utils import get_allowed_moves
import numpy as np
import logging
from heapq import heappush, heappop
import hashlib
from queue import PriorityQueue
from collections import OrderedDict, namedtuple

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# load model
def load_model():

        state_dim = 54
        nnet = ResnetModel(state_dim, 6, 5000, 1000, 4, 1, True).to(device)
        model = "saved_models/model_state_dict.pt"

        state_dict = torch.load(model, map_location=device)
        # remove module prefix
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
                    k = re.sub('^module\.', '', k)
                    new_state_dict[k] = v

        # set state dict
        nnet.load_state_dict(new_state_dict)
            
        # load model
        nnet.eval()
        return nnet
    
nnet = load_model()

class Astart_Node:
    def __init__(self, cube : str, moves : list[Move]):
        self.cube = cube
        self.moves = moves
        self.g = 0
        self.h = 0
        self.f = 0
        self.parent = None
        
    def get_possible_moves(self):
        return get_allowed_moves(self.moves)
    
    def is_solved(self):        
        cube = Cube()
        cube.from_string(self.cube)
        return cube.is_solved()
    
    def update_f(self):
        self.f = 0.6 * self.g + self.h
        
    def __eq__(self, other):
        return self.cube == other.cube
    
def compute_fitness(states):
    # Convert list of states to a NumPy array (if not already an array)
    states_np = np.array(states)
    # Convert NumPy array to a PyTorch tensor
    input_tensor = torch.tensor(states_np, dtype=torch.float32).to(device)
    # Compute output in a single batch
    outputs = nnet(input_tensor)
    fitness_scores = outputs.detach().cpu().numpy()
    torch.cuda.empty_cache()  # Clear CUDA cache here
    return fitness_scores

def sma_star_search(scrambled_str: str, N) -> dict:
    from collections import deque

    open_list = []  # Using deque for efficient pop/append operations.
    closed_list = []

    scrambled_cube = Cube()
    scrambled_cube.from_string(scrambled_str)
    initial_h = compute_fitness(np.array([scrambled_cube.convert_res_input()]))[0]
    start_node = Astart_Node(scrambled_str, [])
    start_node.h = initial_h
    start_node.update_f()

    open_list.append(start_node)

    logging.info("Starting SMA* search with scrambled cube state.")

    while open_list:
        # Select the best N nodes based on f-value but ensure memory limit by pruning if necessary
        while len(open_list) + len(closed_list) > N:
            # Remove the worst node from open_list to maintain memory constraints
            worst_node = max(open_list, key=lambda x: x.f)
            open_list.remove(worst_node)
            # Backup the f-value of the pruned node to its parent if necessary
            if worst_node.parent:
                worst_node.parent.f = max(worst_node.parent.f, worst_node.f)
            logging.debug(f"Pruning node with f-value: {worst_node.f} to maintain memory limits.")

        node = min(open_list, key=lambda x: x.f)  # Node with the smallest f value.
        logging.info(f"Expanding node with f-value: {node.f} and moves: {node.moves}")

        if node.is_solved():
            return {"success": True, "solution": node.moves, "length": len(node.moves), "num_nodes": len(closed_list) + len(open_list)}

        open_list.remove(node)
        closed_list.append(node)
        
        batch_states = []
        batch_info = []
            
        allowed_moves = node.get_possible_moves()
            
        for move in allowed_moves:
            new_moves = node.moves + [move]
            tempcube = Cube()
            tempcube.from_string(node.cube)
            tempcube.move(move)

            if tempcube.is_solved():
                    return {"success": True, "solutions": new_moves, "length": len(new_moves), "num_nodes": len(closed_list) + len(open_list)}
                
            batch_states.append(tempcube.convert_res_input())
            batch_info.append((tempcube.to_string(), new_moves, node))
                
        # Convert batch_states to numpy array and compute fitness
        batch_states_np = np.array(batch_states)
        fitness_scores = compute_fitness(batch_states_np)

        for (tempcube_str, new_moves, parent), fitness in zip(batch_info, fitness_scores):
            new_node = Astart_Node(tempcube_str, new_moves)
            new_node.g = parent.g + 1
            new_node.h = fitness
            new_node.update_f()
            new_node.parent = parent

            # Do not add the node if it results in a worse path to an already visited state.
            existing_node = next((n for n in open_list + closed_list if n.cube == new_node.cube), None)
            if existing_node and existing_node.f <= new_node.f:
                continue

            # Replace existing node with the new node if it's better
            if existing_node:
                open_list.remove(existing_node) if existing_node in open_list else closed_list.remove(existing_node)
            
            open_list.append(new_node)
            
        print("Node Searched so far: ", len(closed_list) + len(open_list))

    return {"success": False, "solution": None, "num_nodes": len(closed_list) + len(open_list)}


def idastar_search(scrambled_str: str) -> dict:

    scrambled_cube = Cube()
    scrambled_cube.from_string(scrambled_str)
    initial_h = compute_fitness(np.array([scrambled_cube.convert_res_input()]))[0]
    start_node = Astart_Node(scrambled_str, [])
    start_node.h = initial_h
    start_node.update_f()
    
    threshold = start_node.f

    def search(node : Astart_Node, threshold, depth = 0, max_depth = 40):
        logging.debug(f"Depth {depth}: Threshold: {threshold}, Current Node F: {node.f}")
        
        if depth > 16:
            logging.info(f"Depth: {depth}, Threshold: {threshold}, Current Node F: {node.f}")
        
        if depth > max_depth:
            logging.info(f"Reached maximum depth of {max_depth}.")
            return float('inf')  # Indicating that this path didn't lead to a solution within the depth limit.
        if node.f > threshold:
            logging.debug(f"Depth {depth}: Node f={node.f} exceeds threshold. Returning to previous level.")
            return node.f
        if node.is_solved():
            logging.debug(f"Solution found with {len(node.moves)} moves: {node.moves}")
            return node
        min_threshold = float('inf')
        
        # Batch preparation for parallel fitness computation
        cube_states = []
        cube_info = []
        for move in node.get_possible_moves():
            tempcube = Cube()
            tempcube.from_string(node.cube)
            tempcube.move(move)
            cube_states.append(tempcube.convert_res_input())  # Prepare the cube state for fitness computation
            cube_info.append((tempcube.to_string(), node.moves + [move]))
            
        # Parallel fitness computation for the batch
        fitness_scores = compute_fitness(np.array(cube_states))
        
        for (cube_str, moves), fitness in zip(cube_info, fitness_scores):
            new_node = Astart_Node(cube_str, moves)
            new_node.g = node.g + 1
            new_node.h = fitness
            new_node.update_f()
            
            logging.debug(f"Depth {depth}: Created new node with f={new_node.f} from moves: {moves}.")
            temp = search(new_node, threshold, depth=depth+1, max_depth=max_depth)  # Recursive search call
            
            if isinstance(temp, Astart_Node):  # Solution found
                return temp
            if temp < min_threshold:
                min_threshold = temp
                
        return min_threshold

    logging.info(f"Starting IDA* search with initial threshold: {threshold}")
    while True:
            start_time = time.time()
            result = search(start_node, threshold)
            if isinstance(result, Astart_Node):  # Solution found
                return {"success": True, "solution": result.moves, "num_moves": len(result.moves)}
            if result == float('inf'):
                return {"success": False, "solution": None, "num_moves": 0}
            logging.info(f"No solution under current threshold {threshold}. Increasing threshold to {result}. Time taken: {time.time() - start_time}")
            threshold = result

BeamEntry = namedtuple('BeamEntry', ['fitness', 'node'])

class Beam_Node:
    def __init__(self, cube, moves, fitness, is_solved):
        self.cube = cube
        self.moves = moves
        self.fitness = fitness
        self.is_solved = is_solved
        
    def __lt__(self, other):
        return self.fitness < other.fitness
        
        
def generate_new_generation(generation: PriorityQueue, prevention):
    new_generation = PriorityQueue()
    nodes_searched = 0
    
    batch_states = []
    batch_info = []
    
    while not generation.empty():
        _, node = generation.get()
        allowed_moves = get_allowed_moves(node.moves) if prevention else Cube().get_possible_moves()
        
        for move in allowed_moves:
            new_moves = node.moves + [move]
            tempcube = Cube()
            tempcube.from_string(node.cube)
            tempcube.move(move)
            state = tempcube.convert_res_input()

            if tempcube.is_solved():
                print("Solution found")
                ans_queue = PriorityQueue()
                ans_queue.put((0, Beam_Node(tempcube.to_string(), new_moves, 0, True)))
                return ans_queue, nodes_searched, True

            batch_states.append(state)
            batch_info.append((tempcube.to_string(), new_moves))
            nodes_searched += 1

    fitness_scores = compute_fitness(batch_states)
    for (tempcube_str, new_moves), fitness in zip(batch_info, fitness_scores):
        new_generation.put((fitness, Beam_Node(tempcube_str, new_moves, fitness, False)))

    return new_generation, nodes_searched, False


def beam_search(scrambled_cube: Cube, beam_width=1024, max_depth=100, prevention=True) -> dict:
    root_fitness = compute_fitness([scrambled_cube.convert_res_input()])[0]
    root = Beam_Node(scrambled_cube.to_string(), [], root_fitness, scrambled_cube.is_solved())
    generation = PriorityQueue()
    generation.put((root_fitness, root))
    start_time = time.time()
    node_searched = 0

    for depth in range(max_depth + 1):
        
        print(f"Depth: {depth}, min_fitness: {generation.queue[0][0]}, node_searched: {node_searched}")
        
        if depth == max_depth:
            return {"success": False, "solutions": None, "num_nodes": node_searched, "time_taken": time.time() - start_time}
        
        new_generation, searched_nodes, success = generate_new_generation(generation, prevention)
        
        if success:
            solution_node = new_generation.get()[1]
            return {"success": True, "solutions": solution_node.moves, "num_nodes": node_searched + searched_nodes, "time_taken": time.time() - start_time}
        
        node_searched += searched_nodes
        generation = PriorityQueue()
        
        for _ in range(min(int(beam_width * (1 + (2 * depth)/100)), new_generation.qsize())):
            if new_generation.empty(): 
                break
            generation.put(new_generation.get())
            
    raise Exception("Beam search failed to find a solution")

if __name__ == "__main__":
    from scramble100 import scrambles
    
    cube = Cube()
    cube.move_list(cube.convert_move(scrambles[0]))
    
    logging.info(f"Scramble: {scrambles[0]}")
    
    start_time = time.time()
    print(beam_search(cube, 1911, 35))
    print("Time taken: ", time.time() - start_time)
            
    #     logging.info(f"Scramble {i + 1}: {scramble}")
    
    # success = 0
    # for i, scramble in enumerate(scrambles):
    #     cube = Cube()
    #     cube.from_string(scramble)
        
    #     logging.info(f"Scramble {i + 1}: {scramble}")
        
    #     start_time = time.time()
    #     result = beam_search(cube)
    #     time_taken = time.time() - start_time
        
    #     if result["success"]:
    #         success += 1
    #         logging.info(f"Solution found in {result['num_nodes']} nodes with {result['solutions']} in {time_taken:.2f} seconds.")
    #     else:
    #         logging.info(f"No solution found in {result['num_nodes']} nodes in {time_taken:.2f} seconds.")
            
    # logging.info(f"Success rate: {success}/{len(scrambles)}")