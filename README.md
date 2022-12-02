# Auto Scraper

Automatically generates rules for scraping web pages.
Rules are generated using xpath based on provided examples. The code finds the elements on the page that contain the desired text.
If more than one element contains the same text, the code returns the xpath with the best score

# Example

´´´python
from sample import Sample
from trainer import Trainer

def find_xpaths():
    samples = [
        Sample(
            url='https://quotes.toscrape.com/',
            targets={
                'first_quote': 'The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking',
                'first_quote_author': 'Albert Einstein',
                'second_quote': 'It is our choices, Harry, that show what we truly are, far more than our abilities',
                'second_quote_author': 'J.K. Rowling',
            }
        ),
    ]

    trainer = Trainer(use_selenium=False)
    xpaths = trainer.train(samples)
    for target, xpath in xpaths.items():
        print(f"Best xpath for {target} is '{xpath}'")

    trainer.save_best_xpaths(xpaths, 'best_xpaths.json')
    return xpaths
´´´

´´´python
def scrape_page(url, xpaths):
    import requests
    from bs4 import BeautifulSoup
    from lxml import etree
    # Load page
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Error {response.status_code}: {response.text}')
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    dom = etree.HTML(str(soup), parser=etree.HTMLParser(encoding='utf-8'))
    results = {}
    for target, xpath in xpaths.items():
        results[target] = ' '.join(dom.xpath(xpath))

    return results
´´´

