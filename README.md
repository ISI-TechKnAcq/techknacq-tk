# T

T is a minimal implementation of the TechKnAcq system for generating
reading lists.


## Components

Tools:
- *build-corpus*:
  Given a directory of PDF or text files, create a directory of JSON files
  containing the document text, annotated with the features needed to judge
  their inclusion in a reading list, and download related encyclopedia
  articles, book chapters, and tutorials.
- *concept-graph*:
  Analyze a JSON corpus to return a JSON graph of concepts and documents
  with the features and links needed to find documents for a reading
  list.
- *reading-lists*:
  Given a concept graph, run a simple Flask web service to return reading
  lists for queries. This will include a simple interface and a JSON API.

Libraries:
- *t*:
  All functionality shared by more than one tool.


## Requirements

T runs on Linux and OS X.

Required Python packages:
- NLTK: Natural language processing.
- Wikipedia: Interface to Wikipedia API.
- NoAho: Efficient trie-based text search.
- BeautifulSoup4: XML processing.
- py-bing-search: Web search API.
- slate: Extract text from PDF files.

All required Python packages should be installed with 'pip'.

Slate depends on pdfminer. To deal with version incompatibility:

    sudo pip install --upgrade --ignore-installed slate==0.3 pdfminer==20110515

See https://github.com/timClicks/slate/issues/5 for updates.


## Configuration

Put your ScienceDirect API key in ~/.t/sd.txt.

Put your Bing API key in ~/.t/bing.txt.

Change the file permissions to keep these keys private.


## Design Principles

- Most problems should not be research questions.
- Take things always by their smooth handle: Try published methods first.
- Deviate from a published method when there is a measurable improvement
  worthy of publishing.
- Create as few runnable tools as possible.
- Create as little code as possible.
- Code is Python.
- Documentation is Markdown.
- Data is JSON.
- Text is UTF-8 with Unix line returns.
- External tools are called with Python APIs.
- Code is in one Git repository.


## Code Requirements

- Single quotes.
- Four spaces.
- < 80 columns.
