import streamlit as st
import chromadb
import uuid
import os

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="WhereIsIt? Smart Item Finder",
    page_icon="🔎",
    layout="wide"
)

DB_PATH = "./chroma_db"

# ---------------- DATABASE ----------------
client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name="personal_items"
)

# ---------------- FUNCTIONS ----------------

def add_item(name, category, description, location):
    item_id = str(uuid.uuid4())

    collection.add(
        ids=[item_id],
        documents=[description],
        metadatas=[{
            "name": name,
            "category": category,
            "location": location
        }]
    )
    return True


def search_items(query):
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(5, collection.count())
    )

    matches = []

    if results["ids"]:
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            matches.append({
                "name": metadata["name"],
                "category": metadata["category"],
                "location": metadata["location"],
                "description": results["documents"][0][i],
                "distance": distance
            })

    return matches


def get_items():
    if collection.count() == 0:
        return []

    data = collection.get()

    items = []

    for i in range(len(data["ids"])):
        items.append({
            "id": data["ids"][i],
            "name": data["metadatas"][i]["name"],
            "category": data["metadatas"][i]["category"],
            "location": data["metadatas"][i]["location"],
            "description": data["documents"][i]
        })

    return items


def delete_item(item_id):
    collection.delete(ids=[item_id])


# ---------------- UI ----------------

st.title("🔎 WhereIsIt?")
st.caption("Smart Personal Item Finder powered by ChromaDB & Semantic Search")

items = get_items()

# Dashboard
st.subheader("📊 Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Total Items", len(items))
col2.metric("Categories", len(set(i["category"] for i in items)))
col3.metric("Locations", len(set(i["location"] for i in items)))

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Search",
    "➕ Add Item",
    "📦 Inventory",
    "🗑️ Delete Item"
])

# ---------------- SEARCH ----------------

with tab1:
    st.subheader("Find Your Belongings")

    query = st.text_input(
        "What are you looking for?",
        placeholder="Example: Where is the thing I use to charge my phone?"
    )

    if st.button("Search", key="search_button"):
        if query.strip():
            results = search_items(query)

            if results:
                st.success(f"Found {len(results)} matching items")

                for item in results:
                    with st.container(border=True):
                        st.markdown(f"### 📌 {item['name']}")
                        st.write(f"**Category:** {item['category']}")
                        st.write(f"**Location:** 📍 {item['location']}")
                        st.write(f"**Description:** {item['description']}")
            else:
                st.info("No items found. Try another search.")

# ---------------- ADD ITEM ----------------

with tab2:
    st.subheader("Add a New Item")

    with st.form("add_form"):
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
        location = st.text_input("Where did you keep it?")

        submitted = st.form_submit_button("Add Item")

        if submitted:
            if name and description and location:
                add_item(name, category, description, location)
                st.success(f"Successfully added {name}!")
                st.rerun()
            else:
                st.warning("Please fill in all fields.")

# ---------------- INVENTORY ----------------

with tab3:
    st.subheader("All Belongings")

    items = get_items()

    if items:
        selected_category = st.selectbox(
            "Filter by category",
            ["All"] + sorted(set(i["category"] for i in items))
        )

        filtered_items = items

        if selected_category != "All":
            filtered_items = [
                i for i in items
                if i["category"] == selected_category
            ]

        st.write(f"Showing {len(filtered_items)} items")

        for item in filtered_items:
            with st.container(border=True):
                st.markdown(f"### {item['name']}")
                st.write(f"**Category:** {item['category']}")
                st.write(f"**Location:** {item['location']}")
                st.write(f"**Description:** {item['description']}")
    else:
        st.info("Your inventory is empty. Add your first item!")

# ---------------- DELETE ----------------

with tab4:
    st.subheader("Remove an Item")

    items = get_items()

    if items:
        selected_item = st.selectbox(
            "Select item to delete",
            items,
            format_func=lambda x: f"{x['name']} — {x['location']}"
        )

        if st.button("Delete Selected Item", type="primary"):
            delete_item(selected_item["id"])
            st.success("Item deleted!")
            st.rerun()
    else:
        st.info("No items available to delete.")

st.divider()

st.caption("WhereIsIt? | Smart Item Finder | Powered by ChromaDB")

    

   
    


       
        
            
