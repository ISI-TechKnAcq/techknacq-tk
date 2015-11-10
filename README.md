# T

T is a minimal implementation of the TechKnAcq system for generating
reading lists.


## Components

Tools:
- *build-corpus*:
  Given a directory of PDF or text files, create a directory of JSON files
  containing the document text, annotated with the features needed to judge
  their inclusion in a reading list, and download related encyclopedia
  articles and book chapters.
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

T is only supported on Linux and OS X.

Python packages:
- NLTK: nltk.org/install.html
- Wikipedia: https://pypi.python.org/pypi/wikipedia/
- NoAho
- BeautifulSoup4
- py-bing-search

## Design Principles

- Most problems should not be research questions.
- Take things always by their smooth handle: Try published methods
  first.
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
