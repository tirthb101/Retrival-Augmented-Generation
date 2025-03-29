from transformers import AutoTokenizer, AutoModel
import numpy as np
import torch
from utils import clean_text, get_resource_path
from bs4 import BeautifulSoup
import requests
import chromadb
import uuid
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

device = "cuda:0"
collection_name = os.getenv("COLLECTION")
persist_directory = get_resource_path("db")
client = chromadb.PersistentClient(path=persist_directory)
collection = client.create_collection(
    collection_name, get_or_create=True)

model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5").to(device)
embed_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")


def chunking_fucntion(text):
    text = clean_text(text)

    # Split text into sentences (modify if needed)
    sentences = text.strip().split("\n")

    # Generate embeddings for all sentences
    embeddings = [generate_embedings(sentence) for sentence in sentences]

    # Set chunking parameters
    similarity_threshold = 0.7  # Adjust based on use case
    max_chunk_tokens = 100  # Approximate token limit per chunk
    chunk = []
    chunks = []
    current_tokens = 0

    # Process sentences for semantic chunking
    for i in range(len(sentences)):
        chunk.append(sentences[i])
        current_tokens += count_tokens(sentences[i])

        if i < len(sentences) - 1:
            # Cosine similarity
            similarity = np.dot(embeddings[i], embeddings[i + 1])

            if similarity < similarity_threshold or current_tokens >= max_chunk_tokens:
                chunks.append(" ".join(chunk))
                chunk = []
                current_tokens = 0

    # Append last chunk if not empty
    if chunk:
        chunks.append(" ".join(chunk))
    return chunks


def generate_embedings(text):
    intermediate = embed_tokenizer(text, padding=True,
                                   truncation=True, max_length=500, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model(**intermediate)
        embeddings = output.last_hidden_state.mean(dim=1)
        return embeddings.squeeze().cpu().numpy()


# Function to estimate token count (approximation)
def count_tokens(sentence):
    return len(sentence.split())  # Replace with a tokenizer if needed


def scrape_website(url, visited, links_global, links_file, output_file):
    print("Visiting:", url)
    print("Total unique links found so far:", len(links_global))
    print("Total pages visited:", len(visited))

    try:
        response = requests.get(url, timeout=11)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return ""

    soup = BeautifulSoup(response.content, "html.parser")
    chunks = chunking_fucntion(soup.get_text())

    # Print the resulting chunks
    for idx, c in enumerate(chunks):
        # print(f"Chunk {idx+1}: {c}\n")
        output_file.write(f"Chunk {idx+1}: {c}\n".encode("utf-8"))
    print(f"Number of semantic chunks: {len(chunks)}")

    # Extract and process links
    for link in soup.find_all('a', href=True):
        absolute_url = link['href']
        wp_content = ("wp-login", "wp-content", "lostpassword", "wp-admin")
        is_not_wp_content = any(keyword in absolute_url.lower()
                                for keyword in wp_content)
        is_new = absolute_url not in visited and absolute_url not in links_global
        contains_erda = "erda" in absolute_url
        is_http = "http" in absolute_url
        forbidden_extensions = (".pdf", ".jpg", ".png", ".jpeg", "xml")
        is_forbidden_extension = any(ext in absolute_url.lower()
                                     for ext in forbidden_extensions)

        if is_new and contains_erda and is_http and not is_forbidden_extension and not is_not_wp_content:
            links_global.add(absolute_url)
            links_file.write(absolute_url + '\n')


def get_erda_data():
    # Initialize sets and file
    links_global = set()
    visited = set()

    # Open the file for writing links
    with open("debug/links.txt", "w") as linkfile:
        # Seed the crawler with an initial URL
        seed_url = 'https://www.erda.org/'
        links_global.add(seed_url)
        linkfile.write(seed_url + '\n')

        # Scrape websites
        with open("debug/text.txt", "wb") as textfile:
            while links_global:
                url = links_global.pop()
                if url not in visited:
                    visited.add(url)
                    scrape_website(
                        url, visited, links_global, linkfile, textfile)
                if len(visited) >= 200:
                    break


def add_data_to_do():
    with open("debug/text.txt", "rb") as file:
        print(collection.count())
        print(collection.delete(where={"_department": "window"}))
        print(collection.count())

        lines = file.readlines()
        for line in tqdm(lines):
            chunk = str(line).split(":")
            chunk = "".join(chunk[1:])
            embeding = generate_embedings(chunk)
            collection.add(documents=[chunk], ids=str(uuid.uuid4()), embeddings=[
                embeding], metadatas={"_department": "window"})


# get_erda_data()
add_data_to_do()


print(len(collection.get(where={"_department": "window"}, )["documents"]))
