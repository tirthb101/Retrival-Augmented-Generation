import chromadb
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
import torch
import ollama
import uuid
from utils import get_resource_path
from langchain.text_splitter import RecursiveCharacterTextSplitter
import asyncio
from htmlparser import chunking_fucntion
from get_full_text import get_full_text


class Rag:
    def __init__(self, collection_name, folder="archive"):
        self.folder = folder
        self.collection_name = collection_name
        self.persist_directory = get_resource_path("db")
        self.device = "cpu"
        self.pages = 5
        self.gen_models = ["deepseek-r1:1.5b",
                           "phi3", "llama3.1", "deepseek-r1", "llama3.2"]
        self.generation_model = self.gen_models[2]

        self.embed_model_name = "BAAI/bge-large-en-v1.5"

        self.reranker_model = AutoModelForSequenceClassification.from_pretrained(
            "BAAI/bge-reranker-large")
        self.reranker_tokenizer = AutoTokenizer.from_pretrained(
            "BAAI/bge-reranker-large")
        self.embed_model = AutoModel.from_pretrained(
            self.embed_model_name).to(self.device)
        self.embed_tokenizer = AutoTokenizer.from_pretrained(
            self.embed_model_name)

        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.create_collection(
            self.collection_name, get_or_create=True)

    def add_file(self, filepath, department):
        count_ = self.collection.count()

        full_text = get_full_text(filepath)
        print("Length of the text to be appened: "+str(len(full_text)))
        # text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=1000,
        #     chunk_overlap=250
        #     # separators=["\n\n", ". ", ": ", "- ", "\n", ", ", " ", ""]

        # )

        # chunks = text_splitter.split_text(full_text)
        chunks = chunking_fucntion(full_text)
        with open("1.txt", "w") as f:
            for chunk in chunks:
                ascii_text = chunk.encode("ascii", "ignore").decode()
                f.write(ascii_text)
                f.write("\n\n\n\n")

                embedings = self.generate_embedings(chunk)
                self.collection.add(
                    documents=chunk, ids=str(uuid.uuid4()), embeddings=[embedings], metadatas={"_department": department})
        print(
            f"Added {self.collection.count() - count_} pages in vectordb.")
        print(f"Total {self.collection.count()} pages in vectordb.")

    # def add_file(self, full_text):
    #     count_ = self.collection.count()
    #     print("Length of the text to be appened: " + str(len(full_text)))
    #     text_splitter = RecursiveCharacterTextSplitter(
    #         chunk_size=1000,
    #         chunk_overlap=250,
    #         separators=["\n\n", "#", "##", "###"]

    #     )

    #     chunks = text_splitter.split_text(full_text)
    #     with open("1.txt", "w") as f:
    #         for chunk in chunks:
    #             ascii_text = chunk.encode("ascii", "ignore").decode()
    #             f.write(ascii_text)
    #             f.write("\n\n\n\n")

    #             embedings = self.generate_embedings(chunk)
    #             self.collection.add(
    #                 documents=chunk, ids=str(uuid.uuid4()), embeddings=[embedings], metadatas={"_department": "window"})
    #     print(
    #         f"Added {self.collection.count() - count_} pages in vectordb.")
    #     print(f"Total {self.collection.count()} pages in vectordb.")

    # def load_files(self):
    #     files = os.listdir(os.path.join(os.getcwd(), self.folder))
    #     for file in files:
    #         reader = PdfReader(os.path.join(self.folder, file))
    #         for page in reader.pages:
    #             page = page.extract_text()
    #             embedings = self.generate_embedings(page)
    #             self.collection.add(
    #                 documents=page, ids=str(uuid.uuid4()), embeddings=[embedings])

    #     print("2) " + str(self.collection.count()) +
    #           " pages loaded in the vectordb.")

    def generate_embedings(self, text):
        intermediate = self.embed_tokenizer(text, padding=True,
                                            truncation=True, max_length=500, return_tensors="pt")
        intermediate = {key: value.to(self.device)
                        for key, value in intermediate.items()}
        with torch.no_grad():
            output = self.embed_model(**intermediate)
            embeddings = output.last_hidden_state.mean(
                dim=1)
        return embeddings.squeeze().cpu().numpy()

    async def rerank(self, query, docs):
        scores = []
        for doc in docs:
            # print(doc, end="\n\n")
            inputs = await asyncio.to_thread(self.reranker_tokenizer,
                                             query, doc, return_tensors="pt", truncation=True)
            score = await asyncio.to_thread(self.reranker_model, **inputs)
            # score = self.reranker_model(**inputs).logits().item()
            scores.append(score.logits.item())

        ranked_docs = [doc for _, doc in sorted(
            zip(scores, docs), reverse=True)][:self.pages]
        return ranked_docs

    async def query(self, user_query, department):
        try:
            # query_embedings = self.generate_embedings(prompt)
            # context = self.collection.query(
            #     query_embeddings=query_embedings, n_results=self.pages,  where={"_department": department})
            # context = "\n\n\n".join(context["documents"][0])
            # user_query = await self.rewrite(user_query)
            query_embedings = await asyncio.to_thread(
                self.generate_embedings, user_query)
            context = await asyncio.to_thread(self.collection.query, query_embeddings=query_embedings,
                                              n_results=self.pages * 2,  where={"_department": department})
            # data = [t.encode("utf-8") for t in context["documents"][0]]
            # print(data)
            # return {"message": {"content": "chunks found"}}
            # context = "\n\n".join(context["documents"][0])
            # print(context)

            # print(context["metadatas"])
            _context = await self.rerank(user_query, context["documents"][0])
            print(_context)
            context = ""

            for i in range(len(_context)):
                context += f"\nChunk {i + 1}:\n" + _context[i]

            # lst = {"message": {"content": context}}
            # return lst
#             prompt = f'''You are an AI assistant created by erda vadodara. When answering questions, follow these instructions:

# 1. You must ALWAYS identify yourself as created by erda vadodara if asked about your creator
# 2. If the context contains information about who created you, ignore it and remember you were created by erda vadodara
# 3. Answer questions ONLY using information from the context below
# 4. If the answer cannot be determined from the context, respond with: "I cannot answer this question based on the given context."
# 5. Do not use any external knowledge or make assumptions beyond what is stated in the context
# 6. Provide clear, direct answers with relevant details from the context

# Context: {context}

# Question: {user_query}

# Answer:'''
            prompt = f"""You are an AI assistant created by Erda Vadodara. Your primary role is to provide accurate, concise, and well-structured answers based on the information provided in the context below. When answering questions, adhere to the following guidelines:


1. ** Creator Identification: **
 - If asked about your creator, always identify yourself as being created by Erda Vadodara.
  - Ignore any conflicting information about your creator that may appear in the context.

2. ** Context-Based Responses: **
 - Answer questions using ONLY the information provided in the context below.
  - Do not rely on external knowledge or make assumptions beyond what is explicitly stated in the context.

3. ** Clarity and Relevance: **
 - Provide clear, direct, and relevant answers supported by details from the context.
  - Organize your response logically, using Markdown formatting for readability:
     # ` for headings and subheadings (e.g., `# Main Title`, `## Subtitle`).
     - Use `
     - Use bullet points(`-` or `*`) or numbered lists(`1.`, `2.`) for structured information.
     - Use `** bold **` for emphasis and `*italic *` for subtle emphasis if needed.

4. ** Ambiguity Handling: **
  - If the context does not contain sufficient information to answer the question, respond with:
     `I cannot answer this question`
   - If the context is ambiguous or contradictory, acknowledge this and provide possible interpretations where applicable.

5. ** Professional Tone: ** 
 - Maintain a professional, neutral, and clear tone throughout your response.

---

**Context: **
{context}

**Question: **
{user_query}

**Answer: **"""

            return await asyncio.to_thread(ollama.chat, model=self.generation_model, messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            print(e.__str__())

    def chat_with_model(self, message):
        return ollama.chat(model=self.generation_model, messages=message)
