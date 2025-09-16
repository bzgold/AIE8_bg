


import os
import re
import uuid
import time
import numpy as np
from getpass import getpass
from typing import List, Dict, Tuple, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

# OpenAI client
from openai import OpenAI

# Document loaders
try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    import fitz  # Fallback for older installations
import docx  # python-docx

# For running in notebooks without "event loop already running" errors:
try:
    import nest_asyncio
    nest_asyncio.apply()
except Exception:
    # not critical in plain scripts
    pass

###OpenAI API key 
def set_openai_api_key(api_key: str = None) -> OpenAI:
    """
    Sets OPENAI_API_KEY env var and returns an initialized OpenAI client.
    """
    if api_key is None:
        api_key = getpass("OpenAI API Key: ")
    os.environ["OPENAI_API_KEY"] = api_key
    # instantiate client AFTER setting env var
    return OpenAI()

###can load both text and PDF documents, vs. the original which was only .txt
class TextLoader:
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.path = path
        self.encoding = encoding

    def load(self) -> str:
        with open(self.path, "r", encoding=self.encoding) as f:
            return f.read()

class PDFLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> str:
        text_parts = []
        doc = fitz.open(self.path)
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            txt = page.get_text("text")
            text_parts.append(f"\n\n[PAGE {pno+1}]\n{txt}")
        doc.close()
        return "\n".join(text_parts)

class DOCXLoader:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> str:
        doc = docx.Document(self.path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip() != ""]
        return "\n\n".join(paragraphs)


###### This changes the way that the text is split. In the original it did.., whereas this add components to make it more sentence and paragraph awarness


class SimpleTextSplitter:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_end_re = re.compile(r'(?<=[.!?])\s+')

    def split_text(self, text: str) -> List[str]:
        sentences = [s.strip() for s in self.sentence_end_re.split(text) if s.strip()]
        chunks = []
        current = ""
        for s in sentences:
            if len(current) + len(s) + 1 <= self.chunk_size:
                current = (current + " " + s).strip()
            else:
                if current:
                    chunks.append(current)
                if len(s) > self.chunk_size:
                    for i in range(0, len(s), self.chunk_size - self.chunk_overlap):
                        part = s[i:i + (self.chunk_size - self.chunk_overlap)]
                        chunks.append(part)
                    current = ""
                else:
                    current = s
        if current:
            chunks.append(current)

        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = []
            for i, c in enumerate(chunks):
                if i == 0:
                    overlapped.append(c)
                else:
                    prev = overlapped[-1]
                    overlap = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev
                    overlapped.append((overlap + " " + c).strip())
            return overlapped
        return chunks


class VectorDatabase:
    def __init__(self, client: OpenAI, embeddings_model: str = "text-embedding-3-large"):
        self.records: List[Dict[str, Any]] = []
        self.embeddings_model = embeddings_model
        self._norm_cache = None
        self.client = client

    def insert(self, text: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        rec = {
            "id": str(uuid.uuid4()),
            "text": text,
            "embedding": np.asarray(embedding, dtype=np.float32),
            "meta": metadata
        }
        self.records.append(rec)
        self._norm_cache = None

    def _ensure_norms(self):
        if self._norm_cache is None:
            if not self.records:
                self._norm_cache = np.empty((0, 0), dtype=np.float32)
                return
            mats = np.vstack([r["embedding"] for r in self.records])
            norms = np.linalg.norm(mats, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._norm_cache = mats / norms

    def search(self, query_embedding: np.ndarray, k: int = 4) -> List[Tuple[Dict[str, Any], float]]:
        if len(self.records) == 0:
            return []
        self._ensure_norms()
        q = np.asarray(query_embedding, dtype=np.float32)
        qnorm = q / (np.linalg.norm(q) + 1e-12)
        scores = np.dot(self._norm_cache, qnorm)
        top_idx = np.argsort(-scores)[:k]
        results = [(self.records[int(i)], float(scores[int(i)])) for i in top_idx]
        return results

    async def abuild_from_texts(self, list_of_texts: List[Tuple[str, Dict[str, Any]]], batch_size: int = 32):
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i in range(0, len(list_of_texts), batch_size):
                batch = list_of_texts[i:i + batch_size]
                texts = [t for t, _ in batch]
                metas = [m for _, m in batch]
                # call the client's embeddings endpoint in a thread
                def _embed_call():
                    return self.client.embeddings.create(model=self.embeddings_model, input=texts)
                try:
                    embeddings_resp = await loop.run_in_executor(pool, _embed_call)
                except Exception as e:
                    raise RuntimeError(f"Embedding API call failed: {e}")
                # align embeddings explicitly by index (safer than pop)
                for j, item in enumerate(embeddings_resp.data):
                    emb = np.array(item.embedding, dtype=np.float32)
                    text = texts[j]
                    meta = metas[j]
                    self.insert(text, emb, meta)
                # be cooperative with rate limits
                await asyncio.sleep(0.05)


def load_and_chunk_files(file_paths: List[str], splitter: SimpleTextSplitter) -> List[Tuple[str, Dict[str, Any]]]:
    all_chunks = []
    for path in file_paths:
        lower = path.lower()
        if lower.endswith(".pdf"):
            loader = PDFLoader(path)
        elif lower.endswith(".docx"):
            loader = DOCXLoader(path)
        else:
            loader = TextLoader(path)
        raw_text = loader.load()
        chunks = splitter.split_text(raw_text)
        total = len(chunks)
        for i, c in enumerate(chunks):
            meta = {"source": os.path.basename(path), "chunk_index": i, "total_chunks": total}
            all_chunks.append((c, meta))
    return all_chunks

##### RAG pipeline that add in self-reflection and transparency of references
class EnhancedRAG:
    def __init__(self, client: OpenAI, llm_model: str = "gpt-4o-mini", embeddings_model: str = "text-embedding-3-large"):
        self.client = client
        self.llm_model = llm_model
        self.vector_db = VectorDatabase(client=client, embeddings_model=embeddings_model)

    async def ingest_files(self, file_paths: List[str], splitter: SimpleTextSplitter):
        corpus = load_and_chunk_files(file_paths, splitter)
        await self.vector_db.abuild_from_texts(corpus)

    def _build_context_block(self, results: List[Tuple[Dict[str, Any], float]]) -> Tuple[str, List[str]]:
        blocks = []
        source_ids = []
        for i, (rec, score) in enumerate(results, start=1):
            sid = f"SRC-{i}"
            source_ids.append(sid)
            meta = rec["meta"]
            snippet = rec["text"][:1000].replace("\n", " ").strip()
            blocks.append(f"[{sid}] Source: {meta.get('source','unknown')} - chunk {meta.get('chunk_index')}/{meta.get('total_chunks')}\n\n{snippet}\n")
        context_text = "\n\n".join(blocks)
        return context_text, source_ids

    def _call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 800) -> str:
        try:
            resp = self.client.chat.completions.create(model=self.llm_model, messages=messages, temperature=temperature, max_tokens=max_tokens)
            return resp.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")

    def ask(self, user_query: str, k: int = 4, do_self_reflection: bool = True) -> Dict[str, Any]:
        try:
            emb_resp = self.client.embeddings.create(model=self.vector_db.embeddings_model, input=[user_query])
        except Exception as e:
            raise RuntimeError(f"Embedding call failed for query: {e}")
        q_emb = np.array(emb_resp.data[0].embedding, dtype=np.float32)
        results = self.vector_db.search(q_emb, k=k)
        context_text, source_ids = self._build_context_block(results)

        system_msg = {
            "role": "system",
            "content": "You are a helpful assistant answering strictly from the context. Cite every factual claim using (SRC-n). If unsupported, say 'UNSUPPORTED'."
        }
        user_msg = {
            "role": "user",
            "content": f"Context:\n\n{context_text}\n\nQuestion: {user_query}\n\nAnswer using only the context and cite inline (SRC-n). Then list sources used."
        }
        first_answer = self._call_llm([system_msg, user_msg])

        output = {"first_answer": first_answer, "retrieved": [(r['meta'], s) for (r, s) in results]}

        if do_self_reflection:
            verify_system = {"role": "system", "content": "You verify claims against context; be conservative."}
            verify_user = {"role": "user", "content": f"Context:\n\n{context_text}\n\nPrevious answer:\n\n{first_answer}\n\nTask:\n1) Number claims.\n2) For each claim, list supporting SRC tags or UNSUPPORTED.\n3) Produce a revised final answer retaining only supported claims. Return JSON with keys: claims, verification, final_answer."}
            verification_response = self._call_llm([verify_system, verify_user], temperature=0.0, max_tokens=1000)
            output["verification"] = verification_response

            summarizer_system = {"role": "system", "content": "Produce a concise final answer and confidence (0-100)."}
            summarizer_user = {"role": "user", "content": f"Verification output:\n{verification_response}\n\nProduce JSON: {{'final_answer_short':..., 'confidence': <int>}}"}
            summary_response = self._call_llm([summarizer_system, summarizer_user], temperature=0.0, max_tokens=200)
            output["final_summary"] = summary_response

        return output

############### Example
async def demo_pmarca_rag():
    """Demo with PMarcaBlogs.txt and original questions"""
    print("🏢 PMARCA BLOGS RAG DEMO")
    print("=" * 50)
    
    client = set_openai_api_key()  # prompts for key, returns OpenAI client
    files = ["data/PMarcaBlogs.txt"]  # Original text file
    splitter = SimpleTextSplitter(chunk_size=800, chunk_overlap=120)
    rag = EnhancedRAG(client=client, llm_model="gpt-4o-mini", embeddings_model="text-embedding-3-large")

    print(f"📄 Loading: {files[0]}")
    await rag.ingest_files(files, splitter)
    print(f"✅ Loaded {len(rag.vector_db.records)} chunks")
    print("🎉 Vector database ready!")

    # Original questions from the PMarca blogs
    questions = [
        "What is the 'Michael Eisner Memorial Weak Executive Problem'?",
        "What are Marc Andreessen's views on software and technology?",
        "What does he say about startups and entrepreneurship?",
        "What are his thoughts on the future of the internet?",
        "What advice does he give to entrepreneurs and founders?"
    ]

    print("\n🎯 ANSWERING 5 ORIGINAL QUESTIONS")
    print("=" * 50)

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*50}")
        print(f"QUESTION {i}: {question}")
        print('='*50)
        
        try:
            print(f"🔍 Searching for: {question}")
            result = rag.ask(question, k=4, do_self_reflection=True)
            print(f"📊 Found {len(result['retrieved'])} relevant chunks")
            print(f"📝 ANSWER: {result['first_answer']}")
            
            if result.get("verification"):
                print(f"\n🔍 VERIFICATION: {result['verification']}")
            
            if result.get("final_summary"):
                print(f"\n📊 FINAL SUMMARY: {result['final_summary']}")
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
        
        print("-" * 50)

    print("\n🎉 Analysis complete!")
    print("💡 You can now ask additional questions interactively...")

    while True:
        try:
            user_question = input("\n❓ Ask another question about PMarca blogs (or 'quit' to exit): ").strip()
            if user_question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_question:
                continue
                
            print("🔍 Searching and analyzing...")
            result = rag.ask(user_question, k=4, do_self_reflection=True)
            
            print(f"\n📝 ANSWER: {result['first_answer']}")
            if result.get("final_summary"):
                print(f"\n📊 SUMMARY: {result['final_summary']}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def demo_nestle_rag():
    """Demo with Nestle HR PDF"""
    print("🏢 NESTLE HR POLICY RAG DEMO")
    print("=" * 50)
    
    client = set_openai_api_key()  # prompts for key, returns OpenAI client
    files = ["data/the_nestle_hr_policy_pdf_2012.pdf"]  # adjust path
    splitter = SimpleTextSplitter(chunk_size=800, chunk_overlap=120)
    rag = EnhancedRAG(client=client, llm_model="gpt-4o-mini", embeddings_model="text-embedding-3-large")

    print(f"📄 Loading: {files[0]}")
    await rag.ingest_files(files, splitter)
    print(f"✅ Loaded {len(rag.vector_db.records)} chunks")
    print("🎉 Vector database ready!")

    questions = [
        "What is Nestle's approach to employee recruitment and hiring?",
        "What are the main HR policies and principles outlined in this document?",
        "What are the key employee benefits and compensation policies?",
        "What are the company's policies on diversity and inclusion?",
        "How does Nestle handle employee performance management and development?",
    ]

    print("\n🎯 ANSWERING 5 NESTLE QUESTIONS")
    print("=" * 50)

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*50}")
        print(f"QUESTION {i}: {question}")
        print('='*50)
        
        try:
            print(f"🔍 Searching for: {question}")
            result = rag.ask(question, k=4, do_self_reflection=True)
            print(f"📊 Found {len(result['retrieved'])} relevant chunks")
            print(f"📝 ANSWER: {result['first_answer']}")
            
            if result.get("final_summary"):
                print(f"\n📊 FINAL SUMMARY: {result['final_summary']}")
                
        except Exception as e:
            print(f"❌ Error processing question: {e}")
        
        print("-" * 50)

    print(" Analysis complete!")

if __name__ == "__main__":
    import sys
    
    # Choose which demo to run
    if len(sys.argv) > 1 and sys.argv[1] == "nestle":
        asyncio.run(demo_nestle_rag())
    else:
        print("Running PMarca Blogs demo...")
        print("(Use 'python new_rag.py nestle' for Nestle HR policy demo)")
        asyncio.run(demo_pmarca_rag())