import pandas as pd
import numpy as np
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
import json



splitter = RecursiveCharacterTextSplitter(
    chunk_size = 800,
    chunk_overlap  = 100,
    length_function = len,
    is_separator_regex = False,
)