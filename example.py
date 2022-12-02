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

if __name__ == '__main__':
    xpaths = find_xpaths()

    results = scrape_page('https://quotes.toscrape.com/', xpaths)
    if results is not None:
        for target, value in results.items():
            print(f'{target}: {value}')

