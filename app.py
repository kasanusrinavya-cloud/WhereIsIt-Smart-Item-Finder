import os
import uuid

import chromadb
import streamlit as st

st.set_page_config(
    page_title="WhereIsIt? Smart Item Finder",
    page_icon="🔎",
    layout="wide"
)

DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_HOST = os.getenv("CHROMA_HOST", "").strip()
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Optional remote ChromaDB configuration
# CHROMA_HOST="your-remote-chroma-host"
# CHROMA_PORT="8000"

try:
    if CHROMA_HOST:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT
        )
        storage_mode = "Remote ChromaDB"
    else:
        os.makedirs(DB_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=DB_PATH)
        storage_mode = "Local ChromaDB (may reset on cloud restart)"

    collection = client.get_or_create_collection(
        name="personal_items"
    )
    db_error = None

except Exception as exc:
    client, collection = None, None
    db_error = str(exc)
    storage_mode = "Database unavailable"


# Sample inventory (added only if database is empty)
DEMO_ITEMS = [
    (
        "USB-C Charger",
        "Electronics",
        "White fast charger for an Android phone",
        "Study table drawer"
    ),
    (
        "Headphones",
        "Electronics",
        "Wireless headphones for listening to music",
        "Bedroom shelf"
    ),
    (
        "College ID Card",
        "College",
        "Student identification card",
        "Blue wallet"
    ),
    (
        "DBMS Notebook",
        "Stationery",
        "Notebook containing database class notes",
        "College bag"
    ),
    (
        "Water Bottle",
        "Daily Essentials",
        "Reusable drinking water bottle",
        "Kitchen counter"
    ),
    (
        "Umbrella",
        "Daily Essentials",
        "Black umbrella used during rainy weather",
        "Behind main door"
    ),
    (
        "Power Bank",
        "Electronics",
        "Portable battery for charging phone",
        "Handbag"
    ),
    (
        "Pen Drive",
        "Electronics",
        "USB flash drive with files",
        "Laptop bag pocket"
    ),
    (
        "Calculator",
        "Stationery",
        "Calculator for engineering calculations",
        "Study table"
    ),
    (
        "Spectacles",
        "Personal",
        "Reading glasses",
        "Bedside table"
    ),
    (
        "House Keys",
        "Daily Essentials",
        "Keys for the house",
        "Key holder near entrance"
    ),
    (
        "Wireless Mouse",
        "Electronics",
        "Wireless computer mouse",
        "Computer desk"
    ),
]


# Add a new item
def add_item(name, category, description, location):
    item_id = str(uuid.uuid4())

    collection.add(
        ids=[item_id],
        documents=[description],
        metadatas=[
            {
                "name": name,
                "category": category,
                "location": location
            }
        ]
    )


# Populate demo items only when database is empty
def seed_demo_inventory():
    if collection.count() == 0:
        for name, category, description, location in DEMO_ITEMS:
            add_item(
                name,
                category,
                description,
                location
            )


# Semantic search
def search_items(query):
    count = collection.count()

    if count == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(5, count),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    matches = []

    for i, item_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] or {}

        matches.append({
            "id": item_id,
            "name": meta.get("name", "Unnamed item"),
            "category": meta.get("category", "Other"),
            "location": meta.get("location", "Unknown"),
            "description": results["documents"][0][i] or "",
            "distance": results["distances"][0][i]
        })

    return matches


# Retrieve all items
def get_items():
    data = collection.get(
        include=["metadatas", "documents"]
    )

    items = []

    for i, item_id in enumerate(data["ids"]):
        meta = data["metadatas"][i] or {}

        items.append({
            "id": item_id,
            "name": meta.get("name", "Unnamed item"),
            "category": meta.get("category", "Other"),
            "location": meta.get("location", "Unknown"),
            "description": data["documents"][i] or ""
        })

    return items


# Delete an item
def delete_item(item_id):
    collection.delete(ids=[item_id])


# Application UI
st.title("🔎 WhereIsIt?")
st.caption(
    "Smart Personal Item Finder powered by "
    "ChromaDB & Semantic Search"
)


if db_error:
    st.error("Database connection failed. Please check ChromaDB settings.")
    st.code(db_error)
    st.stop()


# Add demo data if empty
seed_demo_inventory()

items = get_items()


# Dashboard
col1, col2, col3 = st.columns(3)

col1.metric("Total Items", len(items))

col2.metric(
    "Categories",
    len({x["category"] for x in items})
)

col3.metric(
    "Locations",
    len({x["location"] for x in items})
)


# Database status
with st.expander("Database status and persistence"):
    st.write("Storage:", storage_mode)

    if not CHROMA_HOST:
        st.warning(
            "This version adds demo inventory when the database "
            "is empty so the app is not blank after a reset. "
            "Local cloud storage is still temporary. To keep your "
            "own changes permanently, configure a remote ChromaDB "
            "host using Streamlit secrets (CHROMA_HOST and CHROMA_PORT)."
        )


# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Search",
    "➕ Add Item",
    "📦 Inventory",
    "🗑️ Delete Item"
])


# SEARCH TAB
with tab1:

    st.subheader("Find Your Belongings")

    query = st.text_input(
        "What are you looking for?",
        placeholder="Example: Where is the thing I use to charge my phone?"
    )

    if st.button("Search", key="search_button"):

        if query.strip():

            results = search_items(query.strip())

            if results:

                st.success(
                    f"Found {len(results)} matching items"
                )

                for item in results:

                    with st.container(border=True):

                        st.markdown(
                            f"### 📌 {item['name']}"
                        )

                        st.write(
                            f"**Category:** {item['category']}"
                        )

                        st.write(
                            f"**Location:** 📍 {item['location']}"
                        )

                        st.write(
                            f"**Description:** {item['description']}"
                        )

            else:
                st.info("No items found. Try another search.")


# ADD ITEM TAB
with tab2:

    st.subheader("Add a New Item")

    with st.form("add_form", clear_on_submit=True):

        name = st.text_input("Item Name")

        category = st.selectbox(
            "Category",
            [
                "Electronics",
                "Stationery",
                "Daily Essentials",
                "College",
                "Personal",
                "Other"
            ]
        )

        description = st.text_area("Description")

        location = st.text_input(
            "Where did you keep it?"
        )

        submitted = st.form_submit_button("Add Item")

        if submitted:

            if name.strip() and description.strip() and location.strip():

                add_item(
                    name.strip(),
                    category,
                    description.strip(),
                    location.strip()
                )

                st.success(
                    f"Successfully added {name.strip()}!"
                )

                st.rerun()

            else:
                st.warning("Please fill in all fields.")


# INVENTORY TAB
with tab3:

    st.subheader("All Belongings")

    items = get_items()

    if items:

        selected_category = st.selectbox(
            "Filter by category",
            ["All"] + sorted(
                {x["category"] for x in items}
            )
        )

        filtered = [
            x for x in items
            if selected_category == "All"
            or x["category"] == selected_category
        ]

        st.write(
            f"Showing {len(filtered)} items"
        )

        for item in filtered:

            with st.container(border=True):

                st.markdown(
                    f"### {item['name']}"
                )

                st.write(
                    f"**Category:** {item['category']}"
                )

                st.write(
                    f"**Location:** {item['location']}"
                )

                st.write(
                    f"**Description:** {item['description']}"
                )

    else:
        st.info("Inventory is empty.")


# DELETE ITEM TAB
with tab4:

    st.subheader("Remove an Item")

    items = get_items()

    if items:

        selected = st.selectbox(
            "Select item to delete",
            items,
            format_func=lambda x:
                f"{x['name']} — {x['location']}"
        )

        if st.button(
            "Delete Selected Item",
            type="primary"
        ):

            delete_item(selected["id"])

            st.success("Item deleted!")

            st.rerun()

    else:
        st.info("No items available to delete.")


st.divider()

st.caption(
    "WhereIsIt? | Smart Item Finder | Powered by ChromaDB"
        )
