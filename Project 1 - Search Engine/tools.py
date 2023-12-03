import requests

from bs4 import BeautifulSoup
from brotli import decompress
from nltk import word_tokenize, pos_tag

def get_word_frequency_list(soup, max_len=10000):
    '''
    Takes in a soup object and creates a dictionary with speech tokens as keys and their frequency as value.
    '''
    
    #tokenize raw text, get frequency and sort it
    tokens = word_tokenize(soup.text)
    tokens = [(token, tokens.count(token)) for token in list(set(tokens))]
    tokens = sorted(tokens, key=lambda x: x[1])
    tokens.reverse()

    #filter tokens for all alnum
    tokens = [token for token in tokens if token[0].isalnum()]
    
    #keeps only the max_len first tokens in the dict, e.g. max_len most frequent
    tokens = tokens[:max_len]

    #return only a list and ignore the frequency integer
    return [token[0] for token in tokens]

def ffwiki_content_parsing(soup):
    '''
    Takes in a soup object and processes the ffwiki response content in a way suitable for this search engine.
    Returns the raw text, a string of empty-space separated nouns, a page title, and a description meta element if present.
    '''

    rawtext = soup.text
    tokenized = word_tokenize(rawtext)
    nouns = " ".join([word for word, tag in pos_tag(tokenized) if tag.startswith('NN')])
    title = soup.title.text
    
    description = ''
    try:
        description = soup.find("meta", {"name": "description"})['content']
    
    except:
        description = rawtext #else we use the raw text as description

    return rawtext, nouns, title, description

def ffwiki_filter(url : str) -> bool:
    '''
    Function to filter urls while crawling the finalfantasywiki domain.
    Ignores urls which lead to content-unrelated pages or pages with data which should not be publicly displayed.
    '''

    #only links which are part of the wiki are followed
    if not url.startswith('https://finalfantasywiki.com/wiki'):
        return False

    #if there is a colon in the relative url, check for extra rules
    if ':' in url.split('https://finalfantasywiki.com/wiki')[-1]:
        #exclude all special pages since they do not contain content but wiki or login info
        if 'special:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we also exclude all files
        if 'file:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we do not collect user data
        if 'user:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we ignore help pages for content creators
        if 'help:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we ignore media
        if 'mediawiki:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we ignore user communications
        if 'user talk:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False

        #we ignore unfinished pages or templates for new pages
        if 'template:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower():
            return False
            
        #exclude pages for the about-us sections and similar as they are not content but wiki details and info
        if 'finalfantasywiki:' in url.split('https://finalfantasywiki.com/wiki')[-1].lower().replace(' ',''):
            return False

    #exclude dynamic URLs
    if '?' in url or '#' in url:
        return False
    
    #if no false was returned before, return True since all rules are adhered to
    return True