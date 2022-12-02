from bs4 import BeautifulSoup
from bs4 import NavigableString
from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service
import requests
import warnings

warnings.filterwarnings("ignore")

class Page():
    '''
    Request and extract features from a page to find the most relevant information
    '''
    def __init__(self, url):
        self.url = url
        self.html = None
        self.text_formating_tags = [
            'b', 'big', 'i', 'small', 'abbr', 'cite', 'code', 'em', 'strong', 'br', 'q', 'sub', 'sup',
        ]
        
    def parse_font_size(self, font_size):
        return int(font_size.replace('px', ''))

    def parse_rgb(self, rgb):
        if 'rgba' in rgb:
            return sum([int(x) for x in rgb.replace('rgba(', '').replace(')', '').split(',')[:-1]])/(255*3)
        else:
            return sum([int(x) for x in rgb.replace('rgb(', '').replace(')', '').split(',')])/(255*3)

    def get_html(self):
        return self.html

    def get_soup(self, html):
        return BeautifulSoup(html, 'lxml')
    
    def get_end_nodes(self, soup):
        '''
        https://stackoverflow.com/questions/54265391/find-all-end-nodes-that-contain-text-using-beautifulsoup4
        '''
        def is_end_node(tag):
            if tag.name not in ["div", "p", "span"]:
                return False
            if isinstance(tag, NavigableString):  # if str return
                return False
            if not tag.text:  # if no text return false
                return False
            else:  # ignore text formating tags
                tags_inside_element = [t for t in tag.find_all(text=False) if t.name not in self.text_formating_tags]
                # if contains only one a tag
                if len(tags_inside_element) == 1 and tags_inside_element[0].name == 'a':
                    return True
                if len(tags_inside_element) > 0:
                    return False
            return True  # if valid it reaches here

        return soup.find_all(is_end_node)

    def generate_xpath_from_soup(self, element):
        components = []
        child = element if element.name else element.parent
        for parent in child.parents:
            siblings = parent.find_all(child.name, recursive=False)
            components.append(
                child.name
                if siblings == [child] else
                '%s[%d]' % (child.name, 1 + siblings.index(child))
            )
            child = parent
        components.reverse()
        return '/%s' % '/'.join(components)

class PageSelenium(Page):
    '''
    Request and extract features from a page to find the most relevant information
    '''
    def __init__(self, url):
        super().__init__(url)
        self.web_driver = webdriver.Edge(service=Service(executable_path=EdgeChromiumDriverManager().install()))
        
    def goto(self, url):
        self.web_driver.get(url)
        self.html = self.web_driver.page_source
        return self.html

    def get_style(self, selector):
        element = self.web_driver.find_element("xpath", selector)
        return element.value_of_css_property('font-size'), \
                element.value_of_css_property('font-style'),\
                element.value_of_css_property('color'), \
                element.get_attribute('class')
    
    def get_location(self, selector):
        element = self.web_driver.find_element("xpath", selector)
        location = self.web_driver.execute_script('return arguments[0].getBoundingClientRect();', element)
        return location['x'], location['y'], location['width'], location['height']

    def get_node_features(self, node):
        xpath = self.generate_xpath_from_soup(node)
        if "noscript" in xpath:
            return None
        
        font_size, font_style, font_color, class_name = self.get_style(xpath)
        x, y, width, height = self.get_location(xpath)
        return {
            'name': node.name,
            'xpath': xpath,
            'text': node.text,
            'font_size': self.parse_font_size(font_size),
            'font_style': font_style,
            'color': self.parse_rgb(font_color),
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'class': class_name
        }

    def extract_information(self):
        _ = self.goto(self.url)
        soup = self.get_soup(self.html)
        end_nodes = self.get_end_nodes(soup)
        features = [self.get_node_features(node) for node in end_nodes]
        self.close()
        return [f for f in features if f is not None]
    
    def close(self):
        self.web_driver.quit()
  
class PageBeautifulSoup(Page):
    '''
    Request and extract features from a page to find the most relevant information
    '''
    def __init__(self, url):
        super().__init__(url)
        
    def goto(self, url):
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            self.html = response.text
        return self.html

    def get_node_features(self, node):
        xpath = self.generate_xpath_from_soup(node)
        if "noscript" in xpath:
            return None
        
        return {
            'name': node.name,
            'xpath': xpath,
            'text': node.text,
        }

    def extract_information(self):
        _ = self.goto(self.url)
        soup = self.get_soup(self.html)
        end_nodes = self.get_end_nodes(soup)
        features = [self.get_node_features(node) for node in end_nodes]
        return [f for f in features if f is not None] 


if __name__ == "__main__":
    import json
    import time
    def main():
        url = 'https://quotes.toscrape.com'
        page = PageBeautifulSoup(url)
        features = page.extract_information()
        json.dump(features, open('features.json', 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
    
    # measure time execution function
    start_time = time.perf_counter()
    main()
    end_time = time.perf_counter()
    print(f"Finished in {end_time - start_time} seconds")
