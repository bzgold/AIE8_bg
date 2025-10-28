"""
Enhanced document loaders from assignment 03
"""
import os
from pathlib import Path
from typing import Iterable, List, Dict, Any
import PyPDF2
import pandas as pd
import json


class EnhancedTextFileLoader:
    """Enhanced text file loader from assignment 03 with better file handling"""
    
    def __init__(self, path: str, encoding: str = "utf-8"):
        self.path = Path(path)
        self.encoding = encoding
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []

    def load(self) -> None:
        """Populate documents from the configured path."""
        self.documents = list(self._iter_documents())
        self.metadata = list(self._iter_metadata())

    def load_file(self) -> None:
        """Load a single file specified by self.path."""
        self.documents = [self._read_text_file(self.path)]
        self.metadata = [self._get_file_metadata(self.path)]

    def load_directory(self) -> None:
        """Load all text files contained within self.path."""
        self.documents = list(self._iter_directory(self.path))
        self.metadata = list(self._iter_directory_metadata(self.path))

    def load_documents(self) -> List[str]:
        """Convenience wrapper returning the loaded documents."""
        self.load()
        return self.documents

    def _iter_documents(self) -> Iterable[str]:
        if self.path.is_dir():
            yield from self._iter_directory(self.path)
        elif self.path.is_file() and self.path.suffix.lower() in [".txt", ".csv", ".json"]:
            yield self._read_text_file(self.path)
        else:
            raise ValueError(
                f"Provided path must be a directory or supported file: {self.path}"
            )

    def _iter_directory(self, directory: Path) -> Iterable[str]:
        for entry in sorted(directory.rglob("*")):
            if entry.is_file() and entry.suffix.lower() in [".txt", ".csv", ".json"]:
                yield self._read_text_file(entry)

    def _read_text_file(self, file_path: Path) -> str:
        if file_path.suffix.lower() == ".txt":
            with file_path.open("r", encoding=self.encoding) as file_handle:
                return file_handle.read()
        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
            return df.to_string()
        elif file_path.suffix.lower() == ".json":
            with file_path.open("r", encoding=self.encoding) as file_handle:
                data = json.load(file_handle)
                return json.dumps(data, indent=2)
        else:
            return ""

    def _iter_metadata(self) -> Iterable[Dict[str, Any]]:
        if self.path.is_dir():
            yield from self._iter_directory_metadata(self.path)
        elif self.path.is_file():
            yield self._get_file_metadata(self.path)

    def _iter_directory_metadata(self, directory: Path) -> Iterable[Dict[str, Any]]:
        for entry in sorted(directory.rglob("*")):
            if entry.is_file() and entry.suffix.lower() in [".txt", ".csv", ".json"]:
                yield self._get_file_metadata(entry)

    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        return {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lower(),
            "modified_time": file_path.stat().st_mtime
        }


class PDFLoader:
    """PDF loader from assignment 03 for traffic reports and documents"""
    
    def __init__(self, path: str):
        self.path = Path(path)
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []

    def load(self) -> None:
        """Populate documents from the configured path."""
        self.documents = list(self._iter_documents())
        self.metadata = list(self._iter_metadata())

    def load_file(self) -> None:
        """Load a single PDF specified by self.path."""
        self.documents = [self._read_pdf(self.path)]
        self.metadata = [self._get_pdf_metadata(self.path)]

    def load_directory(self) -> None:
        """Load all PDF files contained within self.path."""
        self.documents = list(self._iter_directory(self.path))
        self.metadata = list(self._iter_directory_metadata(self.path))

    def load_documents(self) -> List[str]:
        """Convenience wrapper returning the loaded documents."""
        self.load()
        return self.documents

    def _iter_documents(self) -> Iterable[str]:
        if self.path.is_dir():
            yield from self._iter_directory(self.path)
        elif self.path.is_file() and self.path.suffix.lower() == ".pdf":
            yield self._read_pdf(self.path)
        else:
            raise ValueError(
                f"Provided path must be a directory or a .pdf file: {self.path}"
            )

    def _iter_directory(self, directory: Path) -> Iterable[str]:
        for entry in sorted(directory.rglob("*.pdf")):
            if entry.is_file():
                yield self._read_pdf(entry)

    def _read_pdf(self, file_path: Path) -> str:
        with file_path.open("rb") as file_handle:
            pdf_reader = PyPDF2.PdfReader(file_handle)
            extracted_pages = [page.extract_text() or "" for page in pdf_reader.pages]
        return "\n".join(extracted_pages)

    def _iter_metadata(self) -> Iterable[Dict[str, Any]]:
        if self.path.is_dir():
            yield from self._iter_directory_metadata(self.path)
        elif self.path.is_file():
            yield self._get_pdf_metadata(self.path)

    def _iter_directory_metadata(self, directory: Path) -> Iterable[Dict[str, Any]]:
        for entry in sorted(directory.rglob("*.pdf")):
            if entry.is_file():
                yield self._get_pdf_metadata(entry)

    def _get_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        with file_path.open("rb") as file_handle:
            pdf_reader = PyPDF2.PdfReader(file_handle)
            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": ".pdf",
                "page_count": len(pdf_reader.pages),
                "modified_time": file_path.stat().st_mtime
            }


class TrafficDocumentProcessor:
    """Specialized processor for traffic-related documents"""
    
    def __init__(self):
        self.text_loader = EnhancedTextFileLoader("")
        self.pdf_loader = PDFLoader("")
    
    def process_traffic_documents(self, directory_path: str) -> Dict[str, Any]:
        """Process all traffic documents in a directory"""
        
        results = {
            "text_documents": [],
            "pdf_documents": [],
            "combined_text": "",
            "metadata": []
        }
        
        directory = Path(directory_path)
        
        # Process text files
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                if file_path.suffix.lower() == ".txt":
                    loader = EnhancedTextFileLoader(str(file_path))
                    loader.load()
                    results["text_documents"].extend(loader.documents)
                    results["metadata"].extend(loader.metadata)
                elif file_path.suffix.lower() == ".pdf":
                    loader = PDFLoader(str(file_path))
                    loader.load()
                    results["pdf_documents"].extend(loader.documents)
                    results["metadata"].extend(loader.metadata)
        
        # Combine all text
        all_texts = results["text_documents"] + results["pdf_documents"]
        results["combined_text"] = "\n\n".join(all_texts)
        
        return results
    
    def extract_traffic_keywords(self, text: str) -> List[str]:
        """Extract traffic-related keywords from text"""
        
        traffic_keywords = [
            "congestion", "delay", "incident", "accident", "crash", "breakdown",
            "construction", "closure", "detour", "jam", "backup", "bottleneck",
            "speed", "volume", "occupancy", "flow", "density", "reliability",
            "traffic", "highway", "freeway", "interstate", "route", "corridor"
        ]
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in traffic_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    def classify_document_type(self, text: str) -> str:
        """Classify document type based on content"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["incident", "accident", "crash", "emergency"]):
            return "incident_report"
        elif any(word in text_lower for word in ["construction", "maintenance", "work"]):
            return "construction_notice"
        elif any(word in text_lower for word in ["analysis", "report", "summary", "data"]):
            return "analysis_report"
        elif any(word in text_lower for word in ["weather", "rain", "snow", "fog"]):
            return "weather_alert"
        else:
            return "general_traffic"
