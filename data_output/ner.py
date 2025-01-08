import pandas as pd
import numpy as np
from langchain.llms import Ollama
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import uuid
import json
from transformers import pipeline

llm = Ollama(model="mistral")

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 800,
    chunk_overlap  = 100,
    length_function = len,
    is_separator_regex = False,
)

## Roberta based NER
# ner = pipeline("token-classification", model="2rtl3/mn-xlm-roberta-base-named-entity", aggregation_strategy="simple")
ner = pipeline("token-classification", model="dslim/bert-large-NER", aggregation_strategy="simple")

print("Number of parameters ->", ner.model.num_parameters()/1000000, "Mn")

def row2NamedEntities(row):
    # print(row)
    ner_results = ner(row['text'])
    metadata = {'chunk_id': row['chunk_id']}
    entities = []
    for result in ner_results:
        entities = entities + [{'name': result['word'], 'entity': result['entity_group'], **metadata}]
        
    return entities

def dfText2DfNE(dataframe):
    ## Takes a dataframe from the parsed data and returns dataframe with named entities. 
    ## The input dataframe must have a text and a chunk_id column. 

    ## Using swifter for parallelism
    ## 1. Calculate named entities for each row of the dataframe. 
    results = dataframe.apply(row2NamedEntities, axis=1)

    ## Flatten the list of lists to one single list of entities. 
    entities_list = np.concatenate(results).ravel().tolist()

    ## Remove all NaN entities
    entities_dataframe = pd.DataFrame(entities_list).replace(' ', np.nan)
    entities_dataframe = entities_dataframe.dropna(subset=['entity'])

    ## Count the number of occurances per chunk id
    entities_dataframe = entities_dataframe.groupby(['name', 'entity', 'chunk_id']).size().reset_index(name='count')

    return entities_dataframe

from pathlib import Path
print(f'{Path().cwd() = }')
pdf = f'{Path().cwd()}/data_input/cureus-0015-00000040274.pdf'
print(f'{pdf = }')
print(f'{Path(pdf).exists() = }')
loader = PyPDFLoader(pdf)
pages = loader.load_and_split()
print(pages)# loader = PyPDFDirectoryLoader("./data/kesy1dd")

pages = loader.load_and_split(text_splitter=splitter)
len(pages)

rows = []
for page in pages:
    row = {'text': page.page_content, **page.metadata, 'chunk_id': uuid.uuid4().hex}
    rows += [row]

df = pd.DataFrame(rows)
dfne = dfText2DfNE(df)

df_ne = dfne.groupby(['name', 'entity']).agg({'count': 'sum', 'chunk_id': ','.join}).reset_index()
df_ne.sort_values(by='count', ascending=False).head(100).reset_index()

pages[12].page_content

def extractConcepts(prompt: str, model='mistral-openorca:latest'):
    SYS_PROMPT = (
        "Your task is to extract the key entities mentioned in the users input.\n"
        "Entities may include - event, concept, person, place, object, document, organisation, artifact, misc, etc.\n"
        "Format your output as a list of json with the following structure.\n"
        "[{\n"
        "   \"entity\": The Entity string\n"
        "   \"importance\": How important is the entity given the context on a scale of 1 to 5, 5 being the highest.\n"
        "   \"type\": Type of entity\n"
        "}, { }]"
    )
    
    
    
    response, context = llm.(model_name=model, system=SYS_PROMPT, prompt=prompt)
    return json.loads(response)
res = extractConcepts(prompt = pages[22].page_content)
print(res)