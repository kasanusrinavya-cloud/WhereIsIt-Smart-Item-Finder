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


