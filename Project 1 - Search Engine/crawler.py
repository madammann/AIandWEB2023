import requests
import time

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from nltk import word_tokenize

#use this header for pages which do not accept python requests user agent
custom_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html", #we ensure only html responses are handled
    "Accept-Language": "en-US,en;q=0.5", #we accept US and GB english with no preference for each
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive", #we prefer to keep the connection alive for better communication from client side
}

#alternative option for accept 

default_header = {
    "User-Agent": "python-requests/2.31.0 Python/3.10.13",
    "Accept": "text/html", #we ensure only html responses are handled
    "Accept-Language": "en-US,en;q=0.5", #we accept US and GB english with no preference for each
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive", #we prefer to keep the connection alive for better communication from client side
}

class Index:
    def __init__():
        self.dict = dict()
        
    def add_entry(url, keywords):
        pass
        
    def to_database(self):
        pass
        
    def from_database(self):
        pass

def get_word_frequency_dict(raw_text, max_len=100):
    '''
    Takes in a text and creates a dictionary with speech tokens as keys and their frequency as value.
    '''

    #tokenize raw text, get frequency and sort it
    tokens = word_tokenize(raw_text)
    tokens = [(token, tokens.count(token)) for token in list(set(tokens))]
    tokens = sorted(tokens, key=lambda x: x[1])
    tokens.reverse()

    #keeps only the max_len first tokens in the dict, e.g. max_len most frequent
    tokens = tokens[:max_len]
    
    return dict(zip([token[0] for token in tokens],[token[1] for token in tokens]))

class Crawler:
    def __init__(header=default_header, allow_external=False, index_method='word_frequency'):
        '''
        ADD
        '''

        #store key parameters
        self.header = header
        self.allow_external = allow_external
        self.index_method = index_method

        #create variables
        self.visited = [] #will include visited urls
        self.queue = [] #will include a queue of encountered urls
        self.netloc = None #will be used to check if URL is from the same server

    def get_urls_from_content(content):
        '''
        ADD
        '''

        
        return urls
    
    def crawl_page(url):
        '''
        ADD
        '''

        #if the page is not from the same server as the starting page, abort and return empty content
        if not self.allow_external:
            if self.netloc != urlparse(url).netloc:
                return None

        response = requests.get(url, headers=self.header)

        if response.status_code == 200 and response.headers["Content-Type"].startswith("text/html"):
            self.visited += [url] #we add url to visited first to avoid self-referencing later
            
            children_urls = self.get_urls_from_content(response.text) #get urls from the same server which are found in the content of the page
            self.queue +=  list(set(children_urls).difference(set(self.visited))) #add found urls to queue if they are not already visited (faster at adding process since list of urls is much smaller)
            
            return response.text

        #for a bad response code ignore result and don't crawl over this url again
        self.visited += [url]
        
        return None

    def index_page(url, text):
        '''
        ADD
        '''
        pass
    
    def crawl(self, start_url : str, iter_lim=1000000, request_waittime=300):
        '''
        ADD
        Request waittime in miliseconds
        NOTE: This function is not multithreaded even though it could be, this is due to showcase purposes and rate limits making multithreading complicated.
        '''
        
        if not self.allow_external:
            self.netloc = urlparse(start_url).netloc

        self.queue = [start_url]

        #we execute a while-loop which crawls either to a fixed iteration limit or until the queue is exhausted
        iter = 0
        while len(self.queue) > 0 and iter <= iter_lim:
            #tests if the first element of the queue was not visited, if it wasn't, visit it
            if self.queue[0] not in self.visited:
                url = self.queue.pop(0) #removes the first element of queue and returns it, saving it in url
                
                #crawl the page and update queue and visited list in crawl
                time.sleep(request_waittime*0.0001) #for the rate limit, we include the waittime in miliseconds
                
                text = self.crawl_page(url)

                #we only update the index if the response was a success
                if content != None:
                    self.index_page(url, text)
                    
                iter += 1
                
            else:
                self.queue.pop(0) #pops the first element of the queue and does not increment iter count

# response = requests.get("https://vm009.rz.uos.de/crawl/index.html", headers=default_header)
# soup = BeautifulSoup(response.text, "html.parser")
# hrefs = [elem['href'] for elem in soup.find_all("a", href=True)]
# hrefs