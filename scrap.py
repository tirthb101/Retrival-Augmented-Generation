import requests
from bs4 import BeautifulSoup
from RAG import Rag
from utils import get_resource_path, clean_text
import chromadb


def scrape_website(url, visited, links_global, output_file):
    """
    Scrape a website, extract text, and collect links.
    """
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
    data = []

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table", "div", "span", "strong"]):
        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            heading_level = int(tag.name[1])
            data.append(f"\n{'#' * heading_level} {tag.get_text()}")

        elif tag.name == "div" and tag.has_attr("class") and "num" in tag["class"]:
            data.append(f"\n{tag.get_text()}")
        elif tag.name in ["ul", "ol"]:
            #     items = [li.get_text() for li in tag.find_all("li")]
            #     print("items", items)
            #     data.append("\n".join([f" - {item}" for item in items]))
            items = tag.find_all("li")
            for item in items:
                anchor_tag = item.find("a")
                # if anchor_tag:
                #     data.append(
                #         f"\n{anchor_tag.get_text()}")
                # else:
                #     data.append(f"\n - {item.get_text()}")

                if not anchor_tag:
                    data.append(f"\n - {item.get_text()}")
        elif tag.name == "table":
            rows = []
            for row in tag.find_all("tr"):
                cells = [cell.get_text()
                         for cell in row.find_all(["td", "th"])]
                rows.append(" | ".join(cells))
            data.append("\n".join(rows))
        elif tag.name != "div":
            data.append(f"\n{tag.get_text()}")

    data = " ".join(data)

    # Extract and process links
    for link in soup.find_all('a', href=True):
        # href = link['href']
        # absolute_url = urljoin(url, href)
        #   # Resolve relative URLs
        absolute_url = link['href']
        # if absolute_url not in visited and absolute_url not in links_global and 'erda' in absolute_url and 'http' in absolute_url and 'pdf' not in absolute_url and 'jpg' not in absolute_url and 'png' not in absolute_url and 'jpeg' not in absolute_url:
        #     links_global.add(absolute_url)
        #     output_file.write(absolute_url + '\n')
        is_not_wp_content = "wp-content" not in absolute_url
        is_new = absolute_url not in visited and absolute_url not in links_global
        contains_erda = "erda" in absolute_url
        is_http = "http" in absolute_url
        forbidden_extensions = (".pdf", ".jpg", ".png", ".jpeg")
        is_forbidden_extension = any(absolute_url.lower().endswith(
            ext) for ext in forbidden_extensions)

        if is_new and contains_erda and is_http and not is_forbidden_extension and is_not_wp_content:
            links_global.add(absolute_url)
            output_file.write(absolute_url + '\n')

    return data


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
            text_data = []
            while links_global:
                url = links_global.pop()
                if url not in visited:
                    visited.add(url)
                    text = scrape_website(url, visited, links_global, linkfile)
                    cleaned_text = clean_text(text)
                    text_data.append(cleaned_text)
                    textfile.write(cleaned_text.encode(
                        "utf-8") + "\n\n\n\n".encode("utf-8"))
                if len(visited) >= 200:
                    break

    # Print all collected text
    return "\n\n".join(text_data)


if __name__ == "__main__":
    # data = get_erda_data()
    # print(type(data))
    with open("1.txt", "r") as file:
        data = file.read()
        print(len(data))
    collection_name = 'test1'
    persist_directory = get_resource_path("db")
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.create_collection(
        collection_name, get_or_create=True)
    print(collection.count())
    print(collection.delete(where={"_department": "window"}))
    print(collection.count())

    rag = Rag("test1")
    rag.add_file(data)
