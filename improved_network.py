import csv
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import colorsys


def create_taxonomy(taxonomy_str):
    """
    Parse taxonomy string into a dictionary mapping category numbers to their names.
    """
    output = {}
    lines = taxonomy_str.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 4:
            try:
                number = int(line[0])
                mod = line[4:].strip()  # Skip ". - " pattern
                output[number] = mod
            except (ValueError, IndexError):
                print(f"Warning: Could not parse line: {line}")
                continue
    
    return output


def generate_colors(n):
    """Generate n distinct colors for visualization."""
    colors = []
    for i in range(n):
        hue = i / n
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        hex_color = '#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(hex_color)
    return colors


def create_network_graph(file_path):
    """
    Create a network graph from CSV data.
    """
    # Data containers
    taxonomy = {}
    posts_by_cluster = defaultdict(list)
    cluster_stats = defaultdict(lambda: {'likes': [], 'hashtags': [], 'posts': []})
    post_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            print(f"CSV columns found: {reader.fieldnames}")
            
            row_count = 0
            for row in reader:
                row_count += 1
                try:
                    post_num = int(row["post number"])
                    cluster_str = row["types of patterns"].strip()
                    likes = int(row["likes"])
                    hashtags_count = int(row["number of hashtags"])
                    
                    print(f"Processing post {post_num}: clusters='{cluster_str}', likes={likes}")
                    
                    # Store post data
                    post_data[post_num] = {
                        'caption': row["caption"],
                        'url': row["url"],
                        'likes': likes,
                        'hashtags': hashtags_count,
                        'clusters': []
                    }
                    
                    # Parse taxonomy from first row
                    if post_num == 1:
                        taxonomy = create_taxonomy(row["taxonomy"])
                        print(f"Taxonomy parsed: {taxonomy}")
                    
                    # Parse cluster assignments - handle different formats
                    clusters = []
                    if "," in cluster_str:
                        cluster_parts = cluster_str.split(",")
                        for part in cluster_parts:
                            try:
                                clusters.append(int(part.strip()))
                            except ValueError:
                                print(f"Warning: Could not parse cluster '{part.strip()}' for post {post_num}")
                    else:
                        try:
                            clusters = [int(cluster_str)]
                        except ValueError:
                            print(f"Warning: Could not parse cluster '{cluster_str}' for post {post_num}")
                            continue
                    
                    post_data[post_num]['clusters'] = clusters
                    
                    # Update cluster statistics
                    for cluster in clusters:
                        posts_by_cluster[cluster].append(post_num)
                        cluster_stats[cluster]['likes'].append(likes)
                        cluster_stats[cluster]['hashtags'].append(hashtags_count)
                        cluster_stats[cluster]['posts'].append(post_num)
                        
                except (ValueError, KeyError) as e:
                    print(f"Warning: Error processing row {post_num if 'post_num' in locals() else row_count}: {e}")
                    print(f"Row data: {dict(row)}")
                    continue
            
            print(f"Total rows processed: {row_count}")
            print(f"Clusters found: {sorted(posts_by_cluster.keys())}")
            print(f"Posts per cluster: {[(k, len(v)) for k, v in posts_by_cluster.items()]}")
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None, None, None, None
    except Exception as e:
        print(f"Unexpected error reading file: {e}")
        return None, None, None, None
    
    return taxonomy, posts_by_cluster, cluster_stats, post_data


def build_graph(taxonomy, posts_by_cluster, cluster_stats):
    """
    Build NetworkX graph from the processed data.
    """
    G = nx.Graph()
    
    print(f"Building graph with {len(taxonomy)} taxonomy categories...")
    print(f"Clusters with posts: {sorted(posts_by_cluster.keys())}")
    
    # Add taxonomy nodes
    nodes_added = 0
    for cluster_id, cluster_name in taxonomy.items():
        if cluster_id in posts_by_cluster:  # Only add clusters that have posts
            posts = posts_by_cluster[cluster_id]
            stats = cluster_stats[cluster_id]
            
            # Calculate aggregate statistics
            total_likes = sum(stats['likes'])
            avg_likes = total_likes / len(stats['likes']) if stats['likes'] else 0
            total_hashtags = sum(stats['hashtags'])
            avg_hashtags = total_hashtags / len(stats['hashtags']) if stats['hashtags'] else 0
            
            # Add node with attributes
            G.add_node(cluster_id, 
                      label=cluster_name,
                      posts_count=len(posts),
                      total_likes=total_likes,
                      avg_likes=avg_likes,
                      total_hashtags=total_hashtags,
                      avg_hashtags=avg_hashtags,
                      posts=posts)
            nodes_added += 1
            
            print(f"Added node {cluster_id}: {cluster_name} ({len(posts)} posts)")
        else:
            print(f"Skipping cluster {cluster_id}: {cluster_name} (no posts)")
    
    print(f"Total nodes added: {nodes_added}")
    
    # Create edges between clusters that share posts
    clusters = list(G.nodes())
    edges_added = 0
    for i, cluster1 in enumerate(clusters):
        for cluster2 in clusters[i+1:]:
            posts1 = set(posts_by_cluster[cluster1])
            posts2 = set(posts_by_cluster[cluster2])
            shared_posts = posts1.intersection(posts2)
            
            if shared_posts:
                # Edge weight based on number of shared posts
                weight = len(shared_posts)
                G.add_edge(cluster1, cluster2, weight=weight, shared_posts=list(shared_posts))
                edges_added += 1
                print(f"Added edge {cluster1}-{cluster2}: {weight} shared posts")
    
    # If graph is disconnected, add similarity edges based on engagement patterns
    if not nx.is_connected(G) and len(G.nodes()) > 1:
        print("Graph is disconnected. Adding similarity edges based on engagement patterns...")
        
        # Calculate similarity between clusters based on average likes
        similarity_threshold = 0.7  # Clusters with similar engagement patterns
        for i, cluster1 in enumerate(clusters):
            for cluster2 in clusters[i+1:]:
                if not G.has_edge(cluster1, cluster2):  # Don't add if already connected
                    avg1 = G.nodes[cluster1]['avg_likes']
                    avg2 = G.nodes[cluster2]['avg_likes']
                    
                    # Calculate similarity (normalized difference)
                    max_avg = max(avg1, avg2, 1)  # Avoid division by zero
                    similarity = 1 - abs(avg1 - avg2) / max_avg
                    
                    if similarity > similarity_threshold:
                        G.add_edge(cluster1, cluster2, weight=0.5, 
                                  similarity=similarity, edge_type='similarity')
                        edges_added += 1
                        print(f"Added similarity edge {cluster1}-{cluster2}: similarity={similarity:.2f}")
    
    print(f"Total edges added: {edges_added}")
    print(f"Graph is connected: {nx.is_connected(G)}")
    return G


def create_pyvis_network(G, output_file='network_visualization.html'):
    """
    Create an interactive Pyvis network visualization.
    """
    net = Network(height='800px', width='100%', bgcolor='#ffffff', font_color='black')
    
    # Configure physics
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 100},
        "barnesHut": {
          "gravitationalConstant": -8000,
          "centralGravity": 0.3,
          "springLength": 95,
          "springConstant": 0.04,
          "damping": 0.09
        }
      }
    }
    """)
    
    # Generate colors for nodes
    colors = generate_colors(len(G.nodes()))
    
    # Add nodes
    for i, (node_id, node_data) in enumerate(G.nodes(data=True)):
        # Node size based on total likes
        size = max(10, min(50, node_data['total_likes'] / 100))
        
        # Create hover title with statistics
        title = f"""
        <b>{node_data['label']}</b><br>
        Posts: {node_data['posts_count']}<br>
        Total Likes: {node_data['total_likes']:,}<br>
        Avg Likes: {node_data['avg_likes']:.1f}<br>
        Total Hashtags: {node_data['total_hashtags']}<br>
        Avg Hashtags: {node_data['avg_hashtags']:.1f}
        """
        
        net.add_node(node_id, 
                    label=f"{node_id}: {node_data['label'][:20]}...",
                    title=title,
                    size=size,
                    color=colors[i % len(colors)])
    
    # Add edges
    for edge in G.edges(data=True):
        source, target, edge_data = edge
        weight = edge_data['weight']
        
        # Edge width based on weight
        width = max(1, min(10, weight * 2))
        
        # Handle different edge types
        if 'shared_posts' in edge_data:
            # Direct connection through shared posts
            shared_posts = edge_data['shared_posts']
            title = f"Shared posts: {len(shared_posts)} (Posts: {', '.join(map(str, shared_posts))})"
            color = 'darkblue'
        elif 'similarity' in edge_data:
            # Similarity connection
            similarity = edge_data['similarity']
            title = f"Similarity connection (engagement pattern similarity: {similarity:.2f})"
            color = 'lightgray'
            width = max(1, width * 0.5)  # Make similarity edges thinner
        else:
            # Fallback
            title = f"Connection (weight: {weight})"
            color = 'gray'
        
        net.add_edge(source, target, 
                    width=width,
                    title=title,
                    color=color)
    
    # Save and show
    net.show(output_file)
    print(f"Network visualization saved to {output_file}")
    return net


def create_matplotlib_visualization(G):
    """
    Create a static matplotlib visualization.
    """
    plt.figure(figsize=(14, 10))
    
    # Create layout - manual positioning to avoid NetworkX version issues
    nodes = list(G.nodes())
    n = len(nodes)
    
    if n == 0:
        print("No nodes to display")
        return
    
    # Create a circular layout manually
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * np.pi * i / n
        pos[node] = (np.cos(angle), np.sin(angle))
    
    # If there are edges, adjust layout to bring connected nodes closer
    if G.number_of_edges() > 0:
        # Use a simple force-directed adjustment
        for _ in range(60):  # Simple iterations
            new_pos = pos.copy()
            for node1, node2 in G.edges():
                # Pull connected nodes closer
                x1, y1 = pos[node1]
                x2, y2 = pos[node2]
                dx = x2 - x1
                dy = y2 - y1
                dist = np.sqrt(dx*dx + dy*dy)
                if dist > 0:
                    force = 0.025
                    new_pos[node1] = (x1 + force * dx, y1 + force * dy)
                    new_pos[node2] = (x2 - force * dx, y2 - force * dy)
            pos = new_pos
    
    # Node sizes based on total likes
    node_sizes = []
    node_colors = []
    for node in G.nodes():
        size = max(300, min(2000, G.nodes[node]['total_likes'] / 5))
        node_sizes.append(size)
        # Color based on number of posts
        post_count = G.nodes[node]['posts_count']
        intensity = min(1.0, post_count / 20)  # Normalize to max 20 posts
        node_colors.append(plt.cm.Blues(0.3 + 0.7 * intensity))
    
    # Edge widths based on weight
    edge_widths = []
    edge_colors = []
    for edge in G.edges(data=True):
        weight = edge[2]['weight']
        width = max(1, min(8, weight * 2))
        edge_widths.append(width)
        
        # Different colors for different edge types
        if 'shared_posts' in edge[2]:
            edge_colors.append('darkblue')  # Direct connections
        else:
            edge_colors.append('lightgray')  # Similarity connections
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                          node_color=node_colors, alpha=0.8, linewidths=2)
    
    if G.number_of_edges() > 0:
        nx.draw_networkx_edges(G, pos, width=edge_widths, 
                              alpha=0.6, edge_color=edge_colors)
    
    # Add labels with better formatting
    labels = {}
    for node in G.nodes():
        label = f"{node}\n{G.nodes[node]['label'][:12]}...\n({G.nodes[node]['posts_count']} posts)"
        labels[node] = label
    
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')
    
    plt.title("Fashion Pattern Modification Network\n(Node size = total likes, Color intensity = post count)", 
              size=14, pad=20)
    plt.axis('off')
    
    # Add legend
    legend_text = []
    for node in sorted(G.nodes()):
        node_data = G.nodes[node]
        legend_text.append(f"Cluster {node}: {node_data['label']} ({node_data['posts_count']} posts, {node_data['total_likes']} likes)")
    
    plt.figtext(0.02, 0.02, '\n'.join(legend_text), fontsize=8, verticalalignment='bottom')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.25)  # Make room for legend
    plt.show()


def print_graph_statistics(G):
    """
    Print detailed statistics about the graph.
    """
    print("\n" + "="*50)
    print("NETWORK GRAPH STATISTICS")
    print("="*50)
    
    print(f"Number of nodes (clusters): {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Graph is connected: {nx.is_connected(G)}")
    
    if G.number_of_nodes() > 0:
        print(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    
    print("\nCluster Details:")
    print("-" * 30)
    for node_id in sorted(G.nodes()):
        node_data = G.nodes[node_id]
        print(f"Cluster {node_id}: {node_data['label']}")
        print(f"  Posts: {node_data['posts_count']}")
        print(f"  Total Likes: {node_data['total_likes']:,}")
        print(f"  Avg Likes: {node_data['avg_likes']:.1f}")
        print()


def main():
    """
    Main function to run the network analysis.
    """
    # Get file input
    file_name = input("Please enter file name ending with .csv: ")
    
    print("Processing inputted data...")
    taxonomy, posts_by_cluster, cluster_stats, post_data = create_network_graph(file_name)
    
    if taxonomy is None:
        return
    
    print("Building your graph...")
    G = build_graph(taxonomy, posts_by_cluster, cluster_stats)
    
    if G.number_of_nodes() == 0:
        print("Warning: No valid clusters found. Check your data format.")
        return
    
    # Print statistics
    print_graph_statistics(G)
    
    # Create visualizations
    print("Creating an interactive visualization...")
    create_pyvis_network(G, 'improved_network.html')
    
    print("Creating a static visualization...")
    create_matplotlib_visualization(G)
    
    print("\nThe analysis is complete!")


if __name__ == "__main__":
    main()