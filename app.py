
import os
import uuid
import gradio as gr
import chromadb
from sentence_transformers import SentenceTransformer

# ---------------- CONFIGURATION ----------------
DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
os.makedirs(DB_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(
    name="personal_items",
    metadata={"hnsw:space": "cosine"}
)

model = SentenceTransformer("all-MiniLM-L6-v2")

# ---------------- INITIAL DATA ----------------
sample_items = [
    ("USB-C Charger", "Electronics", "White fast charger for Android", "Study table drawer"),
    ("Headphones", "Electronics", "Wireless headphones for listening to music", "Bedroom shelf"),
    ("College ID Card", "College", "Student identification card", "Blue wallet"),
    ("Notebook", "Stationery", "DBMS class notes notebook", "College bag"),
    ("Water Bottle", "Daily Essentials", "Reusable water bottle", "Kitchen counter"),
    ("Umbrella", "Daily Essentials", "Black umbrella for rainy weather", "Behind main door"),
    ("Power Bank", "Electronics", "Portable battery for charging devices", "Handbag"),
    ("Pen Drive", "Electronics", "USB flash drive for storing files", "Laptop bag pocket"),
    ("Calculator", "Stationery", "Calculator for engineering calculations", "Study table"),
    ("Spectacles", "Personal", "Eyeglasses for reading and vision", "Bedside table"),
    ("Keys", "Daily Essentials", "House keys", "Key holder near entrance"),
    ("Mouse", "Electronics", "Wireless computer mouse", "Computer desk"),
    ("Sticky Notes", "Stationery", "Small notes used for reminders", "Study table organizer"),
    ("Lunch Box", "Daily Essentials", "Food container for carrying lunch", "Kitchen cabinet"),
    ("Laptop", "Electronics", "Laptop used for programming and projects", "Laptop desk")
]

if collection.count() == 0:
    for item in sample_items:
        item_id = str(uuid.uuid4())
        text = " ".join(item)
        collection.add(
            ids=[item_id],
            documents=[text],
            embeddings=[model.encode(text).tolist()],
            metadatas=[{
                "name": item[0],
                "category": item[1],
                "description": item[2],
                "location": item[3]
            }]
        )

# ---------------- HELPERS ----------------
def all_items():
    data = collection.get()
    rows = []
    for m in data["metadatas"]:
        rows.append([m["name"], m["category"], m["description"], m["location"]])
    return rows

def dashboard():
    items = all_items()
    categories = {}
    for item in items:
        categories[item[1]] = categories.get(item[1], 0) + 1

    category_text = "\n".join(
        [f"- **{category}:** {count}" for category, count in categories.items()]
    )
    return f"## Total Items: {len(items)}\n\n{category_text}"

def search_items(query):
    if not query.strip():
        return "Enter a search query first."

    result = collection.query(
        query_embeddings=[model.encode(query).tolist()],
        n_results=min(5, collection.count())
    )

    output = []
    for metadata, distance in zip(
        result["metadatas"][0], result["distances"][0]
    ):
        similarity = max(0, 1 - distance)
        if similarity >= 0.25:
            output.append(
                f"### {metadata['name']}\n"
                f"📍 **Location:** {metadata['location']}\n"
                f"📂 **Category:** {metadata['category']}\n"
                f"📝 {metadata['description']}\n"
                f"🎯 Match score: {similarity:.2f}\n"
            )

    return "\n---\n".join(output) if output else "No close matches found."

def add_item(name, category, description, location):
    if not all([name, category, description, location]):
        return "Please fill in all fields."

    text = f"{name} {category} {description} {location}"
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[text],
        embeddings=[model.encode(text).tolist()],
        metadatas=[{
            "name": name,
            "category": category,
            "description": description,
            "location": location
        }]
    )
    return f"Successfully added **{name}**!"

def inventory():
    rows = all_items()
    if not rows:
        return "Inventory is empty."
    return "\n".join(
        [f"**{r[0]}** | {r[1]} | {r[2]} | 📍 {r[3]}" for r in rows]
    )

def update_item(old_name, new_name, category, description, location):
    if not old_name:
        return "Enter the current item name."

    data = collection.get()
    found = None
    for i, metadata in enumerate(data["metadatas"]):
        if metadata["name"].lower() == old_name.lower():
            found = data["ids"][i]
            break

    if found is None:
        return f"Item **{old_name}** not found."

    if not all([new_name, category, description, location]):
        return "Fill in all updated details."

    text = f"{new_name} {category} {description} {location}"
    collection.update(
        ids=[found],
        documents=[text],
        embeddings=[model.encode(text).tolist()],
        metadatas=[{
            "name": new_name,
            "category": category,
            "description": description,
            "location": location
        }]
    )
    return f"Successfully updated **{old_name}**."

def delete_item(name):
    if not name:
        return "Enter an item name."

    data = collection.get()
    for i, metadata in enumerate(data["metadatas"]):
        if metadata["name"].lower() == name.lower():
            collection.delete(ids=[data["ids"][i]])
            return f"Successfully deleted **{name}**."

    return f"Item **{name}** not found."

# ---------------- GRADIO UI ----------------
with gr.Blocks(title="WhereIsIt? Smart Item Finder", theme=gr.themes.Soft()) as app:

    gr.Markdown("""
    # 🔎 WhereIsIt?
    ### Smart Personal Item Finder using Vector Database & Semantic Search
    Find belongings using natural language instead of remembering exact item names.
    """)

    with gr.Tab("Dashboard"):
        dashboard_output = gr.Markdown()
        refresh_dashboard = gr.Button("Refresh Dashboard")
        app.load(dashboard, outputs=dashboard_output)
        refresh_dashboard.click(dashboard, outputs=dashboard_output)

    with gr.Tab("Smart Search"):
        search_query = gr.Textbox(
            label="What are you looking for?",
            placeholder="Example: I need something when it rains"
        )
        search_button = gr.Button("Search", variant="primary")
        search_output = gr.Markdown()
        search_button.click(search_items, inputs=search_query, outputs=search_output)
        search_query.submit(search_items, inputs=search_query, outputs=search_output)

    with gr.Tab("Add Item"):
        name = gr.Textbox(label="Item Name")
        category = gr.Textbox(label="Category")
        description = gr.Textbox(label="Description")
        location = gr.Textbox(label="Where did you place it?")
        add_button = gr.Button("Add Item", variant="primary")
        add_output = gr.Markdown()
        add_button.click(
            add_item,
            inputs=[name, category, description, location],
            outputs=add_output
        )

    with gr.Tab("Inventory"):
        inventory_button = gr.Button("View Inventory")
        inventory_output = gr.Markdown()
        inventory_button.click(inventory, outputs=inventory_output)

    with gr.Tab("Edit Item"):
        old_name = gr.Textbox(label="Current Item Name")
        new_name = gr.Textbox(label="Updated Item Name")
        new_category = gr.Textbox(label="Updated Category")
        new_description = gr.Textbox(label="Updated Description")
        new_location = gr.Textbox(label="Updated Location")
        edit_button = gr.Button("Update Item", variant="primary")
        edit_output = gr.Markdown()
        edit_button.click(
            update_item,
            inputs=[old_name, new_name, new_category, new_description, new_location],
            outputs=edit_output
        )

    with gr.Tab("Delete Item"):
        delete_name = gr.Textbox(label="Item Name to Delete")
        delete_button = gr.Button("Delete Item", variant="stop")
        delete_output = gr.Markdown()
        delete_button.click(delete_item, inputs=delete_name, outputs=delete_output)

    gr.Markdown("---")
    gr.Markdown("**Project:** WhereIsIt? | **Technology:** ChromaDB, Python, Sentence Transformers, Gradio")

app.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860))
)
