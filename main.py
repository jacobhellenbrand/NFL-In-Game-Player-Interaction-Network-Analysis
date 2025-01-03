import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import powerlaw
import numpy as np

df = pd.read_csv('player_play.csv')
def build_network(df, conditions, event_weights):
    """
    Creates a undirected graph based on a csv, edge pair conditions, and weights to be assigned
    """
    graph = nx.Graph()

    for (game_id, play_id), play_data in df.groupby(['gameId', 'playId']):
        print(f"Processing Game ID: {game_id}, Play ID: {play_id}")
        player_data = {condition: None for condition in conditions}
        # Iterate through rows of the play data.
        for _, row in play_data.iterrows():
            for player1_var, player2_var in conditions:
                # Check if the first player (player1) has already been identified
                if player_data[(player1_var, player2_var)] is None:
                    if is_condition_met(row, player1_var):
                        player_data[(player1_var, player2_var)] = row['nflId']
                # If player1 is identified, check for player2
                if player_data[(player1_var, player2_var)] is not None:
                    if is_condition_met(row, player2_var):
                        player2 = row['nflId']
                        player1 = player_data[(player1_var, player2_var)]

                        # Ensure player1 and player2 are distinct
                        if player1 is not None and player2 is not None and player1 != player2:
                            edge_weight = event_weights.get((player1_var, player2_var), 0)

                            # Add edge weights
                            if graph.has_edge(player1, player2):
                                graph[player1][player2]['weight'] += edge_weight
                            else:
                                graph.add_edge(player1, player2, weight=edge_weight)
    return graph

def is_condition_met(row, variable):
    """
    Check if the given condition is met.
    """
    value = row.get(variable)
    # print(f"Checking condition for {variable}: {value}")
    if isinstance(value, bool):
        return value is True
    elif isinstance(value, (int, float)):
        return pd.notna(value) and value >= 1
    return False

# Dictionary of condition pairs
event_pairs = {
    ('hadDropback', 'hadPassReception'): 0,
    ('hadDropback', 'wasTargettedReceiver'): 0,
    ('hadPassReception', 'soloTackle'): 0,
    ('hadPassReception', 'tackleAssist'): 0,
    ('hadRushAttempt', 'soloTackle'): 0,
    ('hadRushAttempt', 'tackleAssist'): 0,
    ('hadDropback', 'hadInterception'): 0,
    ('fumbleLost', 'fumbleRecoveries'): 0,
    ('fumbleLost', 'forcedFumbleAsDefense'): 0,
    ('hadDropback', 'causedPressure'): 0,
    ('pressureAllowedAsBlocker', 'causedPressure'): 0,
    ('hadDropback', 'passDefensed'): 0,
    ('wasTargettedReceiver', 'passDefensed'): 0,
    ('hadDropback', 'quarterbackHit'): 0,
    ('hadDropback', 'sackYardsAsDefense'): 0,
    ('tackleAssist', 'tackleAssist'): 0,
    ('forcedFumbleAsDefense', 'fumbleRecoveries'): 0,
    ('forcedFumbleAsDefense', 'hadPassReception'): 0,
    ('forcedFumbleAsDefense', 'hadRushAttempt'): 0,
    ('hadDropback', 'tackleAssist'): 0,
    ('hadDropback', 'soloTackle'): 0,
}

#Adjust the weight by 10% of the 3 main ball carriers
adjTurn = 18.4 + 8.7 + 2.7

# Dictionary of event values
event_values = {
    'Rush Attempt': 87,
    'hadDropback': 184,
    'wasTargettedReceiver': 37,
    'hadPassReception': 27,
    'soloTackle': 23,
    'tackleAssist': 14,
    'hadInterception': 2 + adjTurn,
    'fumbleLost': 2 + adjTurn,
    'fumbleRecoveries': 1 + adjTurn,
    'forcedFumbleAsDefense': 1 + adjTurn,
    'causedPressure': 10 + adjTurn,
    'pressureAllowedAsBlocker': 16,
    'passDefensed': 3 + adjTurn,
    'quarterbackHit': 4 + adjTurn,
    'sackYardsAsDefense': 18 + adjTurn,
}

# Calculate new values for each pair
updated_event_pairs = {}
for (event1, event2), _ in event_pairs.items():
    value1 = event_values.get(event1, 0)
    value2 = event_values.get(event2, 0)
    new_value = 10 / (value1 + value2)
    updated_event_pairs[(event1, event2)] = new_value

conditions = [
    ('hadDropback', 'hadPassReception'),
    ('hadDropback', 'wasTargettedReceiver'),
    ('hadPassReception', 'soloTackle'),
    ('hadPassReception', 'tackleAssist'),
    ('hadRushAttempt', 'soloTackle'),
    ('hadRushAttempt', 'tackleAssist'),
    ('hadDropback', 'hadInterception'),
    ('fumbleLost', 'fumbleRecoveries'),
    ('fumbleLost', 'forcedFumbleAsDefense'),
    ('forcedFumbleAsDefense', 'hadPassReception'),
    ('forcedFumbleAsDefense', 'hadRushAttempt'),
    ('hadDropback', 'causedPressure'),
    ('pressureAllowedAsBlocker', 'causedPressure'),
    ('hadDropback', 'passDefensed'),
    ('wasTargettedReceiver', 'passDefensed'),
    ('hadDropback', 'quarterbackHit'),
    ('hadDropback', 'sackYardsAsDefense'),
    ('hadDropback', 'tackleAssist'),
    ('hadDropback', 'soloTackle'),
    ('tackleAssist', 'tackleAssist'),
    ('forcedFumbleAsDefense', 'fumbleRecoveries')
]

# Need to invert conditions for second team in data set to get its edges
inverted_conditions = [(y, x) for x, y in conditions]
all_conditions = conditions + inverted_conditions

symmetric_event_weights = updated_event_pairs.copy()
for (a, b), weight in updated_event_pairs.items():
    symmetric_event_weights[(b, a)] = weight

# ========= Filter for one game =============
specific_game_id = 2022092501 #Bears Vs Texans
df_filtered = df[df['gameId'] == specific_game_id].reset_index(drop=True)


# ======== Build the Network ===========
# Update df here if you want to analyze a more specific network
player_network = build_network(df, all_conditions, symmetric_event_weights)

player_df = pd.read_csv('players.csv')

# Add new columns to make the rows more meaningful
for _, player_row in player_df.iterrows():
    nfl_id = player_row['nflId']
    if nfl_id in player_network.nodes:
        # Add player name/position to the node
        player_network.nodes[nfl_id]['name'] = player_row['displayName']
        player_network.nodes[nfl_id]['position'] = player_row['position']
for _, row in df.iterrows():
    nfl_id = row['nflId']
    if nfl_id in player_network.nodes:
        # Add team abbreviation as a node attribute
        player_network.nodes[nfl_id]['team'] = row['teamAbbr']

# ======== Visualization of Network ============
# Visualizes the network and saves an edge and node csv to your computer
# Note: csv's are not distinct will rewrite every time code is run

print(f"Player Interaction Network: {len(player_network.nodes)} nodes, {len(player_network.edges)} edges")
nx.draw(player_network, with_labels=True, node_size=500, node_color="orange", font_size=8)
plt.title("Player Interaction Network")
plt.show()

# ========= Download CSV's =============
# This was the download path for my computer, need to update for your own
downloads_path = os.path.expanduser('~/Desktop/Math-479')
node_data = [(nfl_id, data['name'], data['position'], data.get('team')) for nfl_id, data in player_network.nodes(data=True)]
node_data_df = pd.DataFrame(node_data, columns=['ID', 'Label', 'Position', 'Team'])
node_data_df.to_csv(os.path.join(downloads_path, 'player_network_nodes.csv'), index=False)

edges_data = [(player1, player2, data['weight']) for player1, player2, data in player_network.edges(data=True)]
edges_data_df = pd.DataFrame(edges_data, columns=['Source', 'Target', 'Weight'])
edges_data_df.to_csv(os.path.join(downloads_path, 'player_network_edges.csv'), index=False)

def get_degree_distribution(graph):
    """
    Extracts the degree distribution from a NetworkX graph.
    """
    weighted_degrees = [degree for _, degree in graph.degree(weight='weight')]
    return weighted_degrees

def visualize_cumulative_degree_distribution(degrees, name):
    """
    Visualize the cumulative degree distribution on linear and log-log scales.
    """
    unique_degrees, counts = np.unique(degrees, return_counts=True)

    cumulative_counts = np.cumsum(counts[::-1])[::-1]
    cumulative_distribution = cumulative_counts / sum(counts)

    # Linear scale
    plt.figure(figsize=(8, 6))
    plt.plot(unique_degrees, cumulative_distribution, 'o')
    plt.xlabel("Degree")
    plt.ylabel("Cumulative Fraction of Nodes")
    plt.title(f'Cumulative Degree Distribution of {name}')
    plt.show()

    # Log-log scale
    plt.figure(figsize=(8, 6))
    plt.loglog(unique_degrees, cumulative_distribution, 'o')
    plt.xlabel("Degree")
    plt.ylabel("Cumulative Fraction of Nodes")
    plt.title(f'Log-Log Cumulative Degree Distribution of {name}')
    plt.show()

def fit_power_law(degrees, name):
    """
    Fit a power law to the degree distribution and print alpha and xmin values.
    """
    fit = powerlaw.Fit(degrees, discrete=True)
    print(f"The alpha value for {name}: {fit.alpha}")
    print(f"The xmin value for {name}: {fit.xmin}")

    plt.figure(figsize=(8, 6))
    fit.plot_pdf(label='Empirical Data', color='blue')
    fit.power_law.plot_pdf(label='Power Law Fit', color='orange')
    plt.xlabel("Degree")
    plt.ylabel("PDF")
    plt.legend()
    plt.title(f'Power Law Fit for {name}')
    plt.show()

# Calls the functions above, create 3 plots to visualize network degree dist.
degrees = get_degree_distribution(player_network)
visualize_cumulative_degree_distribution(degrees, "Player Network")
fit_power_law(degrees, "Player Network")