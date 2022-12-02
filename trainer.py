from page import PageSelenium, PageBeautifulSoup
from bs4 import BeautifulSoup
from lxml import etree
import numpy as np
from tqdm import tqdm
import json

class Trainer():
    '''
    Find best xpath for dataset
    If use_selenium=True, the page is rendered using selenium
    Else the page is rendered using beautifulsoup

    Selenium is slower but can render javascript pages. Just use selenium if you need to render javascript pages.
    Otherwise, use beautifulsoup.
    '''
    def __init__(self, use_selenium=False) -> None:
        self.samples = None
        self.use_selenium = use_selenium

    def build_train_dataset(self, samples):
        '''
        Build dataset for training
        Go to each sample url and extract all features from the page
        '''
        dataset = []
        for sample in samples:
            train_data = {}
            url = sample.get_url()
            if self.use_selenium:
                page = PageSelenium(url)
            else:
                page = PageBeautifulSoup(url)
            train_data['target'] = sample.get_targets()
            train_data['features'] = page.extract_information()
            train_data['html'] = page.get_html()
            dataset.append(train_data)

        return dataset
        
    def train(self, samples):
        '''
        Build a model to extract information from a page
        We select all the xpaths that contains the target value. 
        Because the webpage can have different layouts, we select all the xpaths that contains the target value.
        Then we evaluate each xpath model in all samples and select the best model for each target.
        '''
        self.samples = samples
        print("Building train dataset...")
        dataset = self.build_train_dataset(samples)

        print('Training...')
        candidates_xpaths = {}  
        for dataset_sample in tqdm(dataset):
            targets = dataset_sample['target']
            features = dataset_sample['features']

            for key, value in targets.items():
                candidates_xpaths[key] = []
                for feature in features:
                    if value.lower() in feature['text'].lower() or value.lower() == feature['text'].lower():
                        if feature['xpath'] not in candidates_xpaths[key]:
                            candidates_xpaths[key].append(feature['xpath']+'//text()')

                if not candidates_xpaths[key]:
                    print(f'Warning: No xpath candidates found for target: {key}')

        print('Finding best xpath...')
        best_xpath = self.find_best_xpath(candidates_xpaths, dataset)
        return best_xpath

    def evaluate_xpath(self, xpath_model, dataset, target_key):
        '''
        Evaluate xpath model in all dataset samples
        If xpath find the target value, the score is incremented by 1 / (lenght of string)
        We penalize the score if the xpath find a string that is too large. Because we want more specific xpaths.
        '''
        score = 0
        for dataset_sample in dataset:
            targets = dataset_sample['target']
            html = dataset_sample['html']

            soup = BeautifulSoup(html, "html.parser")
            dom = etree.HTML(str(soup), parser=etree.HTMLParser(encoding='utf-8'))
            # search value in html using xpath_model[key]
            # value_predict = dom.xpath(xpath_model)[0].text
            value_predict = ''.join(dom.xpath(xpath_model))
            if targets[target_key] in value_predict:
                score += 1 / len(value_predict) # penalize if the model find text with larger strings, looking for shorter strings
        score /= len(dataset)
        return score
        
    def find_best_xpath(self, candidate_xpaths, dataset):
        '''
        Iterate over all xpath models and select the best model for each target
        '''
        targets = dataset[0]['target']
        best_xpaths = {}
        for key, _ in targets.items():
            # search value in all samples usign xpath_models[key]
            scores = []
            if not candidate_xpaths[key]:
                print(f'Warning: No xpath found for target: {key}')
                continue

            for idx, xpath_model in enumerate(candidate_xpaths[key]):
                # evalute each model in all dataset
                scores.append(self.evaluate_xpath(xpath_model, dataset, key))
            # select the best score
            # if there are equal scores, select the first
            idx = np.argmax(scores)
            best_xpaths[key] = candidate_xpaths[key][idx]
                       
        return best_xpaths   

    def save_best_xpaths(self, xpath, filename):
        '''
        Save best xpaths in a file
        '''
        with open(filename, 'w') as f:
            json.dump(xpath, f, ensure_ascii=False, indent=4)