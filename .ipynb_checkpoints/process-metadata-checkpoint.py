import json
import networkx as nx
import numpy as np
import trimesh
import random
from collections import defaultdict
import os

from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def load_graph(path):
    nav_data_path = EXPORT_METADATA_PATH = os.path.join(path, 'nav_grid.json')
    with open(nav_data_path, 'r') as f:
        graph_data = json.load(f)
    
    G = nx.Graph()
    
    for idx, node in enumerate(graph_data['nodes']):
        G.add_node(idx, x=node['position']['x'], y=node['position']['y'], z=node['position']['z'], floor=node['floor'])
    
    for edge in graph_data['edges']:
        u, v = edge['from'], edge['to']
        pos_u = np.array([G.nodes[u]['x'], G.nodes[u]['y'], G.nodes[u]['z']])
        pos_v = np.array([G.nodes[v]['x'], G.nodes[v]['y'], G.nodes[v]['z']])
        distance = np.linalg.norm(pos_u - pos_v)
        
        G.add_edge(u, v, weight=1.0 / (distance + 1e-5), distance=distance)
    
    isolated_nodes = [node for node, degree in dict(G.degree()).items() if degree == 0]
    G.remove_nodes_from(isolated_nodes)
    
    print(f"Removed {len(isolated_nodes)} unconnected/out-of-bounds nodes.")
    print(f"Sanitized Graph: {G.number_of_nodes()} active nodes, {G.number_of_edges()} edges")

    return G

def compute_grid_edge_redundancy(G):
    """
    Computes grid-square redundancy for a 4-connected grid.
    Counts how many 4-cycles (squares) an edge is a part of.
    """
    edge_redundancy = {}
    for u, v in G.edges():
        # Get neighbors of u (excluding v)
        neighbors_u = set(G.neighbors(u)) - {v}
        # Get neighbors of v (excluding u)
        neighbors_v = set(G.neighbors(v)) - {u}
        
        # Find 2-step paths: neighbors of u's neighbors that are also neighbors of v
        common_two_step = []
        for n_u in neighbors_u:
            # Shared neighbors between u's neighbor and v's neighborhood
            shared = set(G.neighbors(n_u)).intersection(neighbors_v)
            if shared:
                common_two_step.extend(list(shared))
                
        # The number of unique square loops flanking this edge
        edge_redundancy[(u, v)] = len(set(common_two_step))
        
    return edge_redundancy

def flood_fill_grid_rooms(G, min_redundancy=1, min_room_size=10):
    """
    Advanced flood-fill for 4-connected grids.
    
    Parameters:
    - min_redundancy: Controls choke sensitivity. 
                      0 = Only split at 1-node-wide doors.
                      1 = Split at 1 or 2-node-wide openings.
                      2 = Highly aggressive splitting.
    - min_room_size: Automatically merges corridors/dead-ends smaller than this tile count.
    """
    grid_squares = compute_grid_edge_redundancy(G)
    
    def is_valid_room_edge(u, v):
        count = grid_squares.get((u, v), grid_squares.get((v, u), 0))
        return count >= min_redundancy

    room_labels = {node: -1 for node in G.nodes()}
    current_room_id = 0
    unassigned_nodes = set(G.nodes())
    
    while unassigned_nodes:
        start_node = random.choice(list(unassigned_nodes))
        queue = [start_node]
        room_labels[start_node] = current_room_id
        unassigned_nodes.remove(start_node)
        
        while queue:
            current_node = queue.pop(0)
            
            for neighbor in G.neighbors(current_node):
                if neighbor in unassigned_nodes:
                    if not is_valid_room_edge(current_node, neighbor):
                        continue
                    
                    room_labels[neighbor] = current_room_id
                    unassigned_nodes.remove(neighbor)
                    queue.append(neighbor)
                    
        current_room_id += 1
        
    # Run the post-processing step to dissolve dead-ends and narrow corridors
    if min_room_size > 0:
        room_labels = merge_small_rooms(G, room_labels, min_room_size)
        
    return room_labels

def merge_small_rooms(G, room_labels, min_room_size=10):
    """Merges any room with fewer than min_room_size nodes into its largest neighbor."""
    # Count sizes of each room
    room_sizes = {}
    for node, r_id in room_labels.items():
        room_sizes[r_id] = room_sizes.get(r_id, 0) + 1
        
    # Find rooms that are too small
    small_rooms = [r_id for r_id, size in room_sizes.items() if size < min_room_size]
    
    for s_room in small_rooms:
        # Find all nodes in this small room
        s_nodes = [n for n, r_id in room_labels.items() if r_id == s_room]
        
        # Look for neighboring nodes that belong to a DIFFERENT room
        neighbor_rooms = []
        for n in s_nodes:
            for neighbor in G.neighbors(n):
                r_neighbor = room_labels[neighbor]
                if r_neighbor != s_room:
                    neighbor_rooms.append(r_neighbor)
                    
        if neighbor_rooms:
            # /Find the most common neighboring room ID and swallow the small room into it
            most_common_neighbor = max(set(neighbor_rooms), key=neighbor_rooms.count)
            for n in s_nodes:
                room_labels[n] = most_common_neighbor
                
    return room_labels

def find_chokepoints(G):
    # Initialize structures to hold our chokepoint data
    chokepoint_nodes = set()
    room_connections = defaultdict(set)
    
    # Iterate through every edge in the graph
    for u, v in G.edges():
        room_u = G.nodes[u]['room_id']
        room_v = G.nodes[v]['room_id']
        
        # If the edge spans across two different room IDs
        if room_u != room_v:
            # Mark both nodes as part of the chokepoint zone
            chokepoint_nodes.add(u)
            chokepoint_nodes.add(v)
            
            # Store which room pairs this node connects (sorted to avoid duplicate pairs like (1,0) and (0,1))
            room_pair = tuple(sorted((room_u, room_v)))
            room_connections[room_pair].add(u)
            room_connections[room_pair].add(v)
    
    # Convert to list for easy matplotlib/networkx drawing usage
    chokepoint_nodes_list = list(chokepoint_nodes)
    
    print(f"Extracted {len(chokepoint_nodes_list)} individual chokepoint tiles.")
    print(f"Discovered {len(room_connections)} unique doorway/passage transitions between rooms:")
    
    for rooms, nodes in room_connections.items():
        print(f"  Portals connecting Room {rooms[0]} <-> Room {rooms[1]}: {len(nodes)} tiles wide.")
    return chokepoint_nodes_list, room_connections

def make_topo_graph(G, room_connections):
        
    # 1. Initialize the high-order topological graph
    topo_G = nx.Graph()
    
    # 2. Add high-level room nodes and calculate their spatial centers
    # This gives the macro-nodes an accurate coordinate for 2D visualization
    for room_id in set(nx.get_node_attributes(G, 'room_id').values()):
        # Gather all grid coordinates belonging to this specific room
        room_nodes = [n for n, attr in G.nodes(data=True) if attr['room_id'] == room_id]
        
        avg_x = np.mean([G.nodes[n]['x'] for n in room_nodes])
        avg_z = np.mean([G.nodes[n]['z'] for n in room_nodes])
        topo_G.add_node(room_id, room_id=room_id, x=avg_x, z=avg_z, size=len(room_nodes))
    
    # 3. Add edges representing the doorways/chokepoints between rooms
    # We use the 'room_connections' dictionary extracted in the previous step
    for (room_a, room_b), portal_nodes in room_connections.items():
        # The weight or width can represent how wide the doorway actually is in grid units
        doorway_width = len(portal_nodes)
        # CRITICAL FIX: Only connect edges if BOTH nodes exist in our valid room set
        if room_a in topo_G and room_b in topo_G:
            topo_G.add_edge(room_a, room_b, doorway_width=doorway_width)
        else:
            # This handles edge cases where post-processing merged a room away
            print(f"Skipping stale portal edge between merged/removed rooms: {room_a} <-> {room_b}")
    
    print("Higher-Order Topological Graph Created Successfully.")
    print(f"Total Rooms (Nodes): {topo_G.number_of_nodes()}")
    print(f"Total Doorways/Connections (Edges): {topo_G.number_of_edges()}")

def plot_rooms_and_chokepoints(G, chokepoint_nodes):
    fig, ax = plt.subplots(figsize=(12, 10))
    layout_2d = {node: (data['x'], data['z']) for node, data in G.nodes(data=True)}
    
    # 1. Generate colors based on Room IDs
    room_ids = [G.nodes[node]['room_id'] if 'room_id' in G.nodes[node] else - 1 for node in G.nodes ]
    
    # 3. Draw standard map edges
    nx.draw_networkx_edges(G, pos=layout_2d, ax=ax, edge_color='black', alpha=0.25)
    
    # 2. Draw the rooms (colored by community)
    nx.draw_networkx_nodes(
        G, pos=layout_2d, ax=ax, 
        node_size=25, 
        node_color=room_ids, 
        cmap='tab20', # Clear qualitative colormap for distinct zones
        alpha= 0.4, 
        linewidths=0
    )
    
    
    # 4. Overlay the Chokepoints prominently
    nx.draw_networkx_nodes(
        G, pos=layout_2d, ax=ax,
        nodelist=chokepoint_nodes & G.nodes,
        node_size=60,
        node_color='red',
        edgecolors='black',
        label='Chokepoints'
    )
    
    ax.set_title("room segmentation & chokepoints")
    ax.set_aspect('equal')
    plt.legend()
    plt.show()

def plot_rooms_and_chokepoints_for_floor(G, chokepoint_nodes, floor):
    filtered_nodes = [
        idx for idx, data in G.nodes(data=True) if data['floor'] == 3
    ]
    subgraph = G.subgraph(filtered_nodes).copy()
    plot_rooms_and_chokepoints(subgraph, chokepoint_nodes_list)



def plot_all_floors(G, chokepoint_nodes, output_filename="navmesh_pipeline_output.png"):
    """
    Slices the graph by floor, renders each floor onto a single multi-panel image,
    and automatically saves it to disk.
    """
    # 1. Identify all unique floors present in the graph data
    unique_floors = sorted(list(set(data['floor'] for _, data in G.nodes(data=True) if 'floor' in data)))
    num_floors = len(unique_floors)
    
    if num_floors == 0:
        print("Pipeline Error: No floors found in graph attributes. Ensure DBSCAN floor-slicing ran first.")
        return

    # 2. Configure a dynamic grid layout (up to 3 plots per row)
    cols = min(3, num_floors)
    rows = (num_floors + cols - 1) // cols
    
    # Scale figure size cleanly based on row/column count
    fig, axes = plt.subplots(rows, cols, figsize=(7 * cols, 6 * rows))
    
    # Ensure axes is always a flat array for predictable iteration loop, even if 1D or a single plot
    if num_floors == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # 3. Render each individual floor onto its matching subplot axis
    for idx, floor_id in enumerate(unique_floors):
        ax = axes[idx]
        
        # Isolate the nodes and construct the subgraph for this specific floor
        filtered_nodes = [n for n, data in G.nodes(data=True) if data.get('floor') == floor_id]
        subgraph = G.subgraph(filtered_nodes).copy()
        
        if subgraph.number_of_nodes() == 0:
            ax.axis('off')
            continue
            
        # Extract the 2D layout coordinates (X, Z) for this floor's nodes
        layout_2d = {node: (data['x'], data['z']) for node, data in subgraph.nodes(data=True)}
        
        # Color nodes by their room ID (fall back to -1 if unassigned)
        room_ids = [subgraph.nodes[n].get('room_id', -1) for n in subgraph.nodes]
        
        # Draw the structure: structural edges first, then rooms, then chokepoints
        nx.draw_networkx_edges(subgraph, pos=layout_2d, ax=ax, edge_color='black', alpha=0.25)
        
        nx.draw_networkx_nodes(
            subgraph, pos=layout_2d, ax=ax, 
            node_size=20, 
            node_color=room_ids, 
            cmap='tab20', 
            alpha=0.4, 
            linewidths=0
        )
        
        # Filter the global chokepoints to only those present on this floor's local subgraph view
        local_chokepoints = set(chokepoint_nodes) & set(subgraph.nodes)
        if local_chokepoints:
            nx.draw_networkx_nodes(
                subgraph, pos=layout_2d, ax=ax,
                nodelist=list(local_chokepoints),
                node_size=45,
                node_color='red',
                edgecolors='black',
                linewidths=0.5,
                label='Chokepoints' if idx == 0 else "" # Avoid duplicate labels in global layout legends
            )
            
        # Local subplot structural framing
        ax.set_title(f"Floor Layer: {floor_id}", fontsize=12, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.15)

    # 4. Clean up any leftover empty subplots in the layout grid
    for j in range(num_floors, len(axes)):
        axes[j].axis('off')

    # Add a unified layout arrangement title and clean margins
    fig.suptitle("Automated NavMesh Multi-Floor Topology Pipeline", fontsize=14, fontweight='bold', y=0.98)
    if num_floors == 1 or local_chokepoints:
        fig.legend(loc="upper right", bbox_to_anchor=(0.95, 0.95))
        
    plt.tight_layout()
    
    # 5. Save image asset to disk and close plot context to prevent memory leakage
    plt.savefig(output_filename, dpi=200, bbox_inches='tight')
    plt.close(fig)

def write_output(path, G, chokepoint_nodes_list, room_segmentation, room_connections):
    
    # OUTPUT_DIR = os.path.dirname(path)
    print(f'writing {path}...')
    EXPORT_METADATA_PATH = os.path.join(path, 'nav_processed_metadata.json')
    EXPORT_TOPO_PATH = os.path.join(path, 'nav_topology_graph.json')
    EXPORT_PLOT_PATH = os.path.join(path, 'nav_floor_visualizations.png')
    
    metadata_payload = []
    for node_id, data in G.nodes(data=True):
        metadata_payload.append({
            "id": int(node_id),
            "position": {"x": data['x'], "y": data['y'], "z": data['z']},
            "floor": data['floor'],
            "room_id": data['room_id'],
            "is_chokepoint": node_id in chokepoint_nodes_list
        })
    
    with open(EXPORT_METADATA_PATH, 'w') as f:
        json.dump(metadata_payload, f, indent=4)
    print(EXPORT_METADATA_PATH)
    
    
    # --- PRODUCT 2: Save High-Order Topological Graph JSON (JsonUtility Compatible) ---
    topo_nodes_list = []
    topo_edges_payload = []
    
    # Generate room macro-nodes as a clean list instead of a keyed dictionary
    for r_id in set(room_segmentation.values()):
        r_nodes = [n for n, attr in G.nodes(data=True) if attr['room_id'] == r_id]
        
        topo_nodes_list.append({
            "room_id": int(r_id),
            "center": {
                "x": float(np.mean([G.nodes[n]['x'] for n in r_nodes])),
                "y": float(np.mean([G.nodes[n]['y'] for n in r_nodes])),
                "z": float(np.mean([G.nodes[n]['z'] for n in r_nodes]))
            },
            "tile_count": len(r_nodes)
        })
    
    # Pack connection macro-edges (remains the same)
    for (room_a, room_b), portal_tiles in room_connections.items():
        topo_edges_payload.append({
            "from_room": int(room_a),
            "to_room": int(room_b),
            "doorway_width": len(portal_tiles),
            "chokepoint_node_ids": list(portal_tiles)
        })
    
    # This structure matches the C# TopologicalGraph class fields exactly
    topo_graph_payload = {
        "rooms": topo_nodes_list,
        "connections": topo_edges_payload
    }
    
    with open(EXPORT_TOPO_PATH, 'w') as f:
        json.dump(topo_graph_payload, f, indent=4)
    print(EXPORT_TOPO_PATH)
    
    plot_all_floors(G, chokepoint_nodes_list, output_filename=EXPORT_PLOT_PATH)
    print(EXPORT_PLOT_PATH)
    print()

def process_scene_data(path):
    # Replace with your actual JSON file path or load directly from a string
    
    G = load_graph(path)
    room_segmentation = flood_fill_grid_rooms(G, min_room_size=5, min_redundancy=2)
    nx.set_node_attributes(G, room_segmentation, 'room_id')
    chokepoint_nodes_list, room_connections = find_chokepoints(G)
    print(f"Identified {max(room_segmentation.values()) + 1} grid-bounded rooms.")
    
    topo_G = make_topo_graph(G, room_connections)
    write_output(path, G, chokepoint_nodes_list, room_segmentation, room_connections)


if __name__ == '__main__':
    # --- ROOT DIRECTORY SETUP ---
    PARENT_DIR = '/Users/rfoltz/dev/game-dev/wetworks/Assets/Resources/data/sceneData/'
    
    print(f"Beginning batch traversal under: {PARENT_DIR}")
        
    if not os.path.exists(PARENT_DIR):
        print(f"error: target parent directory path does not exist: {PARENT_DIR}")
        exit(1)
    
    processed_count = 0
    
    # Recursively step down directory chains looking for nav_grid.json matches
    for root, dirs, files in os.walk(PARENT_DIR):
        if 'nav_grid.json' in files:
            print()
            print(f'===== processing {root} =====')
            try:
                process_scene_data(root)
                processed_count += 1
            except Exception as e:
                print(f"Execution Error occurred processing scene path context '{root}': {e}")
                import traceback
                traceback.print_exc()
    
    print("\n==========================================")
    print(f"Batch Processing Complete. Total scenes processed: {processed_count}")
    print("==========================================")