from whoosh import index, fields, scoring, qparser

class InMemoryIndex:
    '''
    An in-memory index which utilizes a dictionary and primitive functionality.
    The dictionary has keywords as keys and a list of urls with said keywords as values.
    '''
    
    def __init__(self):
        self.in_memory_dict = {}
        
    def add_entry(self, keywords, url):
        '''
        Method for adding a keyword and url to the existing dictionary.
        '''
        
        for keyword in keywords:
            if keyword in self.in_memory_dict.keys():
                self.in_memory_dict[keyword] += [url]
                
            else:
                self.in_memory_dict[keyword] = [url]

    def search(self, query):
        '''
        Primitive search method, receives a query string and splits it into keywords.
        Returns a list of all urls which include all the keywords from the search.
        '''

        query_list = query.split(' ') #split into a list of words separated by empty space
        
        #gather the set of urls which are linked to at least one word
        urls = set([])
        for i, word in enumerate(query_list):
            if word in self.in_memory_dict.keys():
                #if urls is still empty, we simply add all urls listed for the first keyword
                if len(urls) != 0:
                    urls = urls.intersection(set(self.in_memory_dict[word])) #we take the intersection to remove urls not present in the next word
                    
                else:
                    urls = set(self.in_memory_dict[word])

            #if even a single keyword is not present in this basic search, we return no urls
            else:
                return []
        
        return list(urls)

class WhooshCustomizedIndex:
    '''
    A whoosh index which is customized to build an index and search for it specifically for the Final Fantasy Wiki page.
    Requires an "index" folder in root, the index stores the raw text of pages, the string of nouns only, the title, the url, and a description.
    '''
    
    def __init__(self, index_directory='./index/', weighting=scoring.TF_IDF()):
        self.weighting = weighting
        self.index_directory = index_directory
        
        self.schema = fields.Schema(
            rawtext = fields.TEXT(stored=True), # A field for storing the raw text from a html
            nouns = fields.KEYWORD(stored=True), # A field for storing the nouns from the text
            title = fields.ID(stored=True, unique=True), # A field for storing the title of the text
            url = fields.TEXT(stored=True), #a field for storing the url
            description = fields.TEXT(stored=True) #field for retrieving, if possible, the description to be shown in the search
)
        try:
            self.index = index.open_dir(self.index_directory)
            
        except:
            self.index = index.create_in(self.index_directory, self.schema)
        
        self.writer = self.index.writer()
        self.qp = qparser.MultifieldParser(["rawtext", "nouns", "title"], self.index.schema, fieldboosts={"title": 2})

    def add_entry(self, rawtext : str, nouns : str, title : str, description : str, url : str):
        '''
        Method for adding an entry to the whoosh index from specified arguments.
        
        param rawtext (str): The raw text of the response for a page.
        param nouns (str): A whitespace-separated string of all nouns from a page.
        param title (str): The title of the page.
        param description (str): The description of the page, if found, else just the rawtext again.
        param url (str): The url of the page.
        '''
        
        if self.writer != None:
            try:
                self.writer.add_document(rawtext = rawtext, nouns = nouns, title = title, url = url, description = description)

            except index.IndexError:
                #if we encounter a page twice, because of redirects, we update the document with the most recent one
                self.writer.update_document(rawtext = rawtext, nouns = nouns, title = title, url = url, description = description)
                
        else:
            raise AttributeError('Index writer object was already destroyed after complete_index was called.')

    def complete_index(self):
        '''
        Finalizes the index by commiting with the writer and also destroying the writer.
        '''
        
        self.writer.commit()
        self.writer = None

    def search(self, query_string : str, search_method=None):
        '''
        Search method which receives a search string and, optionally, a search method from whoosh.scoring, like scoring.TF_IDF().
        A search on this index searches weighing the raw text, the title, and the list of nouns.
        This method returns a tuple of lists, the first list being urls, the second being titles, and the third being descriptions up to 503 chars.

        returns (tuple): (list[str] : url, list[str] : title, list[str] : descriptions) for result in search results.
        '''

        query = self.qp.parse(query_string)
        
        #we search the index with specified weighting and gather the results as tuples of url, title, and description
        #if no search_method is specified, we use the weighting this index was initialized with.
        results_gathered = []
        if search_method == None:
            with self.index.searcher(weighting=self.weighting) as searcher:
                results = searcher.search(query)
                
                for result in results:
                    results_gathered += [(result['url'], result['title'], result['description'][:500]+'...')]
        
        #otherwise we use the specified search method
        else:
            with self.index.searcher(weighting=search_method) as searcher:
                results = searcher.search(query)
                
                for result in results:
                    results_gathered += [(result['url'], result['title'], result['description'][:500]+'...')]

        return [a for a,b,c in results_gathered], [b for a,b,c in results_gathered], [c for a,b,c in results_gathered]