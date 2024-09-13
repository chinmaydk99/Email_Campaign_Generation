import chromadb
import zipfile
import os

def upload_and_extract_zip(zip_name, extract_path):    
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    print(f"Extracted all files to {extract_path}")

def setup_chromadb():
    """
    Sets up ChromaDB collections after uploading and extracting necessary files.
    
    Returns:
    tuple: (product_collection, promotions_collection)
    """

    upload_and_extract_zip("product_research.zip", "/product_research")
    
    upload_and_extract_zip("product_offers.zip", "/product_offers")
    
    product_research_client = chromadb.PersistentClient(path="/product_research")
    product_collection = product_research_client.get_collection("product_research")
    
    promotions_client = chromadb.PersistentClient(path="/product_offers")
    promotions_collection = promotions_client.get_collection("product_offers")
    
    return product_collection, promotions_collection

def query_database(collection, query_text, n_results=2):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results