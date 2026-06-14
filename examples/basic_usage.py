from hermes_okf.bundle import OKFBundle

# Create a new OKF bundle
bundle = OKFBundle("./my_knowledge")

# Write a concept
bundle.write_concept(
    "projects/fifa_pipeline",
    body="# FIFA World Cup Pipeline\n\nExtracts viral clips using ffmpeg and YOLOv8.",
    type="Project",
    title="FIFA World Cup Clip Pipeline",
    tags=["fifa", "ffmpeg", "yolo", "gpu"],
    resource="https://github.com/EliaszDev/fifa-pipeline",
)

# Read it back
concept = bundle.read_concept("projects/fifa_pipeline")
print(f"Title: {concept.title}")
print(f"Tags: {concept.tags}")

# Search by tag
gpu_projects = bundle.search_by_tag("gpu")
print(f"Found {len(gpu_projects)} GPU-related concepts")

# Log an agent action
bundle.append_log("Dropped PyTorch due to ROCm issues on RX 5500 XT", category="Decision")

# Inspect the graph
edges = bundle.get_graph_edges()
for edge in edges:
    print(f"{edge['source']} -> {edge['target']}")
