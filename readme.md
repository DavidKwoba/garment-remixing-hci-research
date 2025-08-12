**Garment Remixing Cycle HCI Research Project - archival code** 
This project was completed as part of a research project that explored how various 
garment makers (tailors, dressmakers, etc) discover, share patterns, and combine the patterns 
they find online (remixing). The project has 2 components which are basically 
scrapping data using the InstaLoader python library and storing it in a csv file, and 
analyzing the data by drawing relationships between clusters of fashion posts 
based on shared characteristics (e.g., style, tags, shared posts). It uses the CSV dataset to 
process the data, build a network graph, and produce both interactive and static visualizations 
along with summary statistics.

**Part 1: Data Scrapping - Instaloader** 
This python script uses the Instaloader library to scrape recent posts from a 
given hashtag (garment pattern name). It downloads the images and saves the captions 
and URL into a CSV file. 

Implementation Approach 
- Fetches up to NUM_POSTS posts for a specific hashtag.
- Filters posts by age (MAX_DAYS old or newer).
- Downloads post images locally.
- Saves post metadata (caption + link) to a CSV file. 

Environment Variables 
This project uses a .env file for credentials 
     - IG_USERNAME=your_username 
     - IG_PASSWORD=your_password 

**Important Notes (2025) **
- Instagram has changed its API and web endpoints since 2022.
- The function get_hashtag_posts() used here may no longer work without modifications, due to:
    - Removal of the ?__a=1 JSON endpoint for hashtags.
    - Stricter login and bot-detection measures.
- Login with username/password from within Instaloader may now fail with Login error: Unexpected response or 404 Not Found for hashtags.
- To run this in 2025, you may need to:
    - Use a saved browser session or cookies instead of direct login.
    - Switch to Instagram GraphQL queries or HTML parsing.

**Part 2: Data Visualization - NetworkX and matplotlib **
Implementation Approach 
Data Input: Read a CSV file containing post/cluster information.
Network Construction: Build a NetworkX graph with clusters as nodes and relationships as edges.
Statistical Summary: Print overall graph metrics and per-cluster statistics (posts, likes, averages).
Static Visualization: Generate a matplotlib plot of the network with size/color encoding for popularity and activity.
Interactive Visualization: Generate a browser-based Pyvis network for exploring node/edge relationships.

**Running the program **
After entering the name of the `.csv` file containing your dataset. The script will:
1. Parse the CSV and construct the graph.
2. Print network statistics to the terminal.
3. Save an interactive HTML visualization (`improved_network.html`).
4. Display a static matplotlib visualization.

You can use the existing CSV files to format your input file. 

**Your output should display: **
The Terminal Statistics: 
- Number of nodes and edges
- Graph connectivity
- Average degree
- Per-cluster details (label, post count, likes, averages)

A Static Visualization: 
- Node size = total likes
- Node color intensity = post count
- Edge thickness = relationship weight
- Edge color = connection type

An Interactive Visualization: 
- HTML file (`improved_network.html`)
- Hover over nodes for details
- Click/drag to explore connections
