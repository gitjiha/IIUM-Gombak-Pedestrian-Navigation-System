import streamlit as st
import heapq
import folium
from streamlit_folium import st_folium

# 1. Page configuration
st.set_page_config(page_title="IIUM Gombak Navigation", layout="wide", initial_sidebar_state="expanded")

# --- CSS ---
st.markdown(
    """
    <style>
    /* This line hides the top navigation bar/header */
    header { visibility: hidden; }

    /* Change the whole page background to a soft turquoise */
    .stApp { 
        background-color: black !important; 
        overflow: hidden !important; 
        max-height: 100vh !important; 
    }
    
    /* Add a gold border around the main container */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        border: 5px solid #FFD700;
        border-radius: 15px;
    }
    /* This targets the sidebar background */
    [data-testid="stSidebar"] {
        background-color: #40E0D0 !important; /* Turquoise */
        border-right: 5px solid #FFD700;      /* Gold border on the right */
    }

    /* This changes the text inside the sidebar to white for readability */
    [data-testid="stSidebar"] * {
        color: black !important;
    }
    
    /* Optional: Change the button color to match your Gold theme */
    div.stButton > button {
        background-color: #FFD700 !important;
        color: black !important;
        border: 2px solid white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- YOUR ORIGINAL CLASS (UNTOUCHED) ---
class IIUMNavigationSystem:
    def __init__(self):
        # Graph stores buildings as nodes, with (neighbor, distance, time) as edges
        self.graph = {
            'KICT': [('MAHALLAH', 1200, 17), ('KOE', 1000, 15), ('KAED', 1000, 15)],
            'MAHALLAH': [('KICT', 1200, 17), ('KOE', 1100, 15), ('KOED', 750, 11)],
            'KOE': [('KICT', 1000, 15), ('MAHALLAH', 1100, 15), ('KOED', 1100, 15), ('ICC', 170, 2)],
            'KAED': [('KICT', 1000, 15), ('ICC', 170, 2)],
            'ICC': [('KOE', 170, 2), ('KAED', 170, 2), ('ADMIN', 450, 6)],
            'KOED': [('MAHALLAH', 750, 11), ('KOE', 1100, 15), ('CAFETERIA', 1000, 15), ('LIBRARY', 650, 9), ('MOSQUE', 850, 11)],
            'CAFETERIA': [('KOED', 1000, 15)],
            'ADMIN': [('ICC', 450, 6), ('MOSQUE', 400, 5)],
            'LIBRARY': [('KOED', 650, 9), ('MOSQUE', 1200, 17)],
            'MOSQUE': [('KOED', 850, 11), ('ADMIN', 400, 5), ('LIBRARY', 1200, 17)]
        }
        # Hash table for quick building info lookup
        self.campus_hash_table = {
            'KICT': { 'name': 'Kulliyyah of Information and Communication Technology', 'id': '8777', 'coordinates': '3.2505° N, 101.7335° E' },
            'MOSQUE': { 'name': 'Sultan Haji Ahmad Shah Mosque', 'id': 'M321', 'coordinates': '3.251025° N, 101.73581° E' },
            'KOE': { 'name': 'Kulliyyah of Engineering', 'id': 'E101', 'coordinates': '3.2520° N, 101.7340° E' },
            'MAHALLAH': { 'name': 'Central Mahallah Complex', 'id': 'M001', 'coordinates': '3.2560° N, 101.7310° E' },
            'ADMIN': { 'name': 'IIUM Administration Building', 'id': 'A001', 'coordinates': '3.2500° N, 101.7380° E' },
            'ICC': { 'name': 'IIUM Cultural Centre', 'id': 'I777', 'coordinates': '3.2508° N, 101.7362° E' },
            'KOED': { 'name': 'Kulliyyah of Education', 'id': 'ED202', 'coordinates': '3.2541° N, 101.7365° E' },
            'LIBRARY': { 'name': 'Dar al-Hikmah Library', 'id': 'L505', 'coordinates': '3.2530° N, 101.7395° E' },
            'KAED': { 'name': 'Kulliyyah of Architecture and Environmental Design', 'coordinates': '3.2515° N, 101.7350° E' },
            'CAFETERIA': { 'name': 'Main Campus Cafeteria', 'coordinates': '3.2535° N, 101.7370° E' }
        }

    def hash_lookup(self, search_key):
        # Normalize input and search hash table
        clean_key = search_key.strip().upper()
        if clean_key in self.campus_hash_table: return self.campus_hash_table[clean_key]
        return None

    def calculate_shortest_path(self, start, destination):
        # Normalize input
        start = start.strip().upper()
        destination = destination.strip().upper()
        # Validate inputs
        if start not in self.graph or destination not in self.graph: return None, float('inf'), float('inf')
        # Priority queue for Dijkstra
        priority_queue = [(0, start, 0, [start])]
        visited = set()
        while priority_queue:
            # Extract smallest distance node
            current_dist, current_node, current_time, path = heapq.heappop(priority_queue)
            # Return result if target is reached
            if current_node == destination: return path, current_dist, current_time
            # Skip if already visited
            if current_node in visited: continue
            visited.add(current_node)
            # Add neighbors to queue
            for neighbor, distance, time in self.graph[current_node]:
                if neighbor not in visited:
                    heapq.heappush(priority_queue, (current_dist + distance, neighbor, current_time + time, path + [neighbor]))
        return None, float('inf'), float('inf')

nav = IIUMNavigationSystem()

# --- INITIALIZATION ---
if 'highlight' not in st.session_state: st.session_state.highlight = None
if 'path' not in st.session_state: st.session_state.path = None

def get_coords(name):
    # Parse coordinates for folium
    meta = nav.campus_hash_table.get(name)
    if not meta: return [3.2525, 101.7345]
    parts = meta['coordinates'].replace('° N,', '').replace('° E', '').split(' ')
    return [float(parts[0]), float(parts[1])]

# --- UI LAYER ---
with st.sidebar:
    st.title("📍 IIUM Gombak Navigation System")
    tab1, tab2 = st.tabs(["Info", "Navigate"])
    with tab1:
        query = st.selectbox("Building:", list(nav.campus_hash_table.keys()))
        if st.button("Search"): 
            st.session_state.highlight = query
            st.session_state.path = None

            # Fetch and display info
            info = nav.campus_hash_table.get(query)
            if info:
                st.write(f"**Name:** {info['name']}")
                st.success(f"📍 {info['coordinates']}") 
    with tab2:
        start = st.selectbox("From:", list(nav.graph.keys()))
        dest = st.selectbox("To:", list(nav.graph.keys()))
        if st.button("Calculate Route", type="primary", use_container_width=True):
            st.session_state.highlight = None
            st.session_state.path, dist, time = nav.calculate_shortest_path(start, dest)
            # Displaying the info
            st.sidebar.success(f"📍 Distance: {dist}m \n⏱️ Time: {time} min ")

# --- MAP AREA ---
m = folium.Map(location=[3.2525, 101.7345], zoom_start=16, dragging=False, scrollWheelZoom=True)
path_set = set(st.session_state.path) if st.session_state.path else set()

for key in nav.campus_hash_table.keys():
    is_active = (key == st.session_state.highlight) or (key in path_set)
    color = "red" if is_active else "blue"
    
    # Add markers
    folium.Marker(get_coords(key), tooltip=key, icon=folium.Icon(color=color, icon="none")).add_to(m)
    
    # Add labels for active nodes
    if is_active:
        folium.map.Marker(
            get_coords(key),
            icon=folium.DivIcon(html=f'''
                <div style="
                    font-size: 10pt; font-weight: bold; color: #CC0000; 
                    white-space: nowrap; transform: translate(-40%, 25px);
                    background-color: rgba(255, 255, 255, 0.7);
                    padding: 2px 4px; border-radius: 4px;
                ">{key}</div>
            ''')
        ).add_to(m)

# Draw polyline for path
if st.session_state.path:
    folium.PolyLine([get_coords(n) for n in st.session_state.path], color="#CC0000", weight=6).add_to(m)

st_folium(m, width="100%", height=500, returned_objects=[])