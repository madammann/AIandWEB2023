import requests
import time

from tqdm import tqdm
from bs4 import BeautifulSoup

from urllib.parse import urlparse, urljoin
from brotli import decompress

from tools import ffwiki_content_parsing, get_word_frequency_list, ffwiki_filter

from index import WhooshCustomizedIndex

#use this header for pages which do not accept python requests user agent
CUSTOM_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html", #we ensure only html responses are handled
    "Accept-Language": "en-US,en;q=0.5", #we accept US and GB english with no preference for each
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive", #we prefer to keep the connection alive for better communication from client side
}

#alternative option for accept 

DEFAULT_HEADER = {
    "User-Agent": "python-requests/2.31.0 Python/3.10.13",
    "Accept": "text/html", #we ensure only html responses are handled
    "Accept-Language": "en-US,en;q=0.5", #we accept US and GB english with no preference for each
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive", #we prefer to keep the connection alive for better communication from client side
}

URL = 'https://finalfantasywiki.com/wiki/Main_Page'

class Crawler:
    '''
    The crawler class for crawling the Final Fantasy Wiki.
    Calling this class optimized is more than just a stretch, but for the sub 10.000 page wiki it suffices.
    There is no multithreading or optimized list management, there is just a queue and a visited list.
    This crawler crawls from a starting page over all internal links and only handles html responses by default.
    '''
    
    def __init__(self, index, header=DEFAULT_HEADER, allow_external=False, filter_func=lambda url: True, index_method=get_word_frequency_list, timeout=60):
        '''
        param index: An index provided, either the InMemoryIndex or the WhooshCustomizedIndex should be provided here.
        param header: The header to use for requests.
        param allow_external (bool): A boolean whether to allow visiting outside references or just references on the same server.
        param filter_func: A parameter which may be overwritten by a function which takes in an url and returns either True or False to decide whether to crawl it or not.
        param index_method: A function which receives a soup object and returns a tuple of filtered information, use the in tools specified FFwiki parser here.
        param timeout (int): A timeout value specified for the requests.
        '''

        #store key parameters
        self.header = header
        self.allow_external = allow_external
        self.index_method = index_method
        self.timeout = timeout
        
        #create variables
        self.index = index
        self.visited = [] #will include visited urls
        self.queue = [] #will include a queue of encountered urls
        self.netloc = None #will be used to check if URL is from the same server
        self.filter = filter_func #a function which receives an url and returns true if this url should be added to the index
    
    def crawl_page(self, url):
        '''
        Method for crawling a specific page, handles errors and internal dynamics with queue and visited list, then returns soup object.
        '''

        #if the page is not from the same server as the starting page, abort and return empty content
        if not self.allow_external:
            if self.netloc != urlparse(url).netloc:
                return None

        #we try to get a response from a, hopefully syntactically correct, url, if errors occur, we avoid that url
        response = None
        try:
            response = requests.get(url, headers=self.header, timeout=self.timeout)
            
        except Exception as e:
            print(e)
            self.visited += [url] #to avoid trying to access faulty url anymore, we add it to visited
            return None

        #we process the content and links only if the response was successful and in html format
        if response.status_code == 200 and response.headers["Content-Type"].startswith("text/html"):
            self.visited += [url] #we add url to visited first to avoid self-referencing later

            #store all href in the html text in a list
            hrefs = [elem['href'] for elem in BeautifulSoup(response.content, "html.parser").find_all("a", href=True)]
            
            #filter complete and relative urls and store both in complete urls after making absolute urls out of the relative ones
            relative_urls = [url for url in hrefs if not url.startswith('http')]
            complete_urls = [url for url in hrefs if url.startswith('http')]
            complete_urls += [urljoin(response.url, relative_url) for relative_url in relative_urls]

            #we filter urls in case we wish to filter our index and exclude certain pages
            complete_urls = [url for url in complete_urls if self.filter(url)]

            #add found urls to queue if they are not already visited (faster at adding process since list of urls is much smaller)
            self.queue +=  list(set(complete_urls).difference(set(self.visited)))
            
            return BeautifulSoup(response.content, "html.parser")

        #for a bad response code ignore result and don't crawl over this url again
        self.visited += [url]
        
        return None

    def index_page(self, url : str, soup):
        '''
        Method for indexing the page, calls the specified index_method function from the initialization.
        Then proceeds to call add_entry on the index with a tuple of the index_method's return value and the url.
        '''

        index_data = self.index_method(soup)
        self.index.add_entry(*(*index_data, url))
    
    def crawl(self, start_url : str, iter_lim=10000, request_waittime=600):
        '''
        Method called to start crawling, crawls from a starting page until iteration limit is reached or references were crawled.
        
        param start_url (str): Url of the first page to crawl.
        param iter_lim (int): Number of maximum iterations allowed for the crawler.
        param request_waittime (int): Request waittime in miliseconds, to set a rate_limit to avoid being blocked out.
        
        NOTE: This function is not multithreaded even though it could be, this is due to showcase purposes and rate limits making multithreading complicated.
        '''
        
        if not self.allow_external:
            self.netloc = urlparse(start_url).netloc

        self.queue = [start_url]

        #we execute a while-loop which crawls either to a fixed iteration limit or until the queue is exhausted
        iter = 0
        pbar = tqdm(total=iter_lim)
        while len(self.queue) > 0 and iter < iter_lim:
            #tests if the first element of the queue was not visited, if it wasn't, visit it
            if self.queue[0] not in self.visited:
                url = self.queue.pop(0) #removes the first element of queue and returns it, saving it in url
                
                #crawl the page and update queue and visited list in crawl
                time.sleep(request_waittime/1000) #for the rate limit, we include the waittime in miliseconds
                
                soup = self.crawl_page(url)

                #we only update the index if the response was a success
                if soup != None:
                    self.index_page(url, soup)
                    
                iter += 1
                pbar.update(1)
                
            else:
                self.queue.pop(0) #pops the first element of the queue and does not increment iter count
        pbar.close()

        #we finalize the index by commiting
        self.index.complete_index()

if __name__ == "__main__":
    crawler = Crawler(WhooshCustomizedIndex(), filter_func=ffwiki_filter, index_method=ffwiki_content_parsing)
    crawler.crawl(URL)