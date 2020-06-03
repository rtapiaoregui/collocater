#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  2 13:41:45 2018

@author: rita

Building the word-collocations dictionary from 
the Online Oxford Collocation Dictionary and the phrases 
from the English Oxford Dictionaries

"""

import requests
import re
from bs4 import BeautifulSoup as bs
import regex
import joblib
import random
import pandas as pd


from lxml.html import fromstring

import pkg_resources as pkr

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span



def store_collocs_in_df(found_colls_dict):
    """
    Function to transform the output of the Collocater class into a data frame.
    """
    
    df_colls = pd.DataFrame(found_colls_dict).T
    
    colls_type_df = df_colls.coll_type.str.split(' / ', expand=False)
    df_colls.rename(columns={'coll_type': 'orig_coll_type'}, inplace=True)

    df_colls1 = pd.concat([df_colls, colls_type_df], axis='columns')
    
    df_colls2 = df_colls1.explode('coll_type')
    
    colls_type_df1 = df_colls2.coll_type.str.split('__', expand=True)
    df_colls3 = pd.concat([df_colls2, colls_type_df1], axis='columns')
    df_colls3.rename(columns={0: 'word_type', 1: 'Type of collocation'}, inplace=True)
    
    df_colls4 = df_colls3.assign(location=df_colls3["location"].map(lambda x: "start: {}; end: {}".format(x[0]+1, x[1])))
    df_colls4 = df_colls4.assign(word_type=df_colls4["word_type"].map(lambda x: "{} ({})".format(x.split('_')[0], x.split('_')[-1])))
    df_colls4.reset_index(inplace=True)
    df_colls4.rename(columns={'index':'collocation', 
                              'word_type': "Morphology of word with collocation", 
                              'location': "Positions of first and last token of collocation"}, inplace=True)
    
    df_colls5 = df_colls4.set_index('Type of collocation')
    df_colls5.rename(index={
                    'prep':'Preposition', 
                    'adj':'Adjective', 
                    'adv':'Adverb', 
                    'pre_verb': 'Object of verb', 
                    'post_verb': 'Subject of verb',
                    'post_noun': 'Appositive',
                    'quant': 'Quantity noun',
                    'phr': 'Phrase'}, inplace = True)

    df_colls5.reset_index(inplace=True)
    
    df_colls6 = df_colls5.set_index('collocation')
    df_colls6.fillna('', inplace=True)
    df_colls6.drop(columns=["orig_coll_type", "coll_type"], inplace=True)
    df_colls6.index.name = None
    coloco = df_colls6.columns.tolist()
    columna = [coloco[-1]] + coloco[:-1]
    found_colls_df = df_colls6[columna]
    
    return found_colls_df     
    
            

def collocations_linker(text, found_collocations, color="rgb(255, 158, 0, 0.4)"):
    """
    Function to transform the text where collocations are meant to be found 
    into a string with html tags to highlight the collocations found.
    """

    all_colls = found_collocations.keys()
        
    all_colls1 = sorted(all_colls, key=len)[::-1]
    
    for col in all_colls1:
        text = regex.sub(r'(?<='+f'{regex.escape(col)})'+r'(?:\b)', '</span>', regex.sub(r'(?:\b)(?='+f'{regex.escape(col)})', f'<span style="background-color: {color}">', text))

    return text
    
    
  
    

class Collocater():
    
    name = "colls"
    
    def __init__(self, 
                 irr_verbs, prepositions, collocations_dictionary=None,
                 chosen_collocation_types=None, chosen_word_types='both',
                 tags_dict=None, spacy_model='en_core_web_sm'):
        
        
        self.spacy_model = spacy_model
        self.irr_verbs = irr_verbs
        self.prepositions = prepositions
        self.chosen_collocation_types = chosen_collocation_types 
        self.chosen_word_types = chosen_word_types

        
        if not collocations_dictionary:
            self.collocations_dictionary = {}
        else:
            self.collocations_dictionary = collocations_dictionary

            
        if not tags_dict:
            self.tags_dict = {'someone': "__PERSON__",
                         'sb_sth': "__OTHER__",
                         'something': "__THING__",
                         'possessive_det': '__PERSON_S__',
                         'one_word': "__WORD__",
                         'this_word': "__THIS_WORD__"
                         }      
        else:
            self.tags_dict = tags_dict
            
    
    
    def loader(path=None):
        """
        Determines where the file is supposed to be found and loads it.
        """
        
        if not path:
            obj = joblib.load(pkr.resource_stream(__name__, 'data/collocater_obj.joblib'))
        else:
            with open(path, 'rb') as fh:
                obj = joblib.load(fh)      
                
        return obj
    
    
            
    def saver(self, path):
        """
        Saves the Collocater Object in the specified file.
        """
        with open(path, 'wb') as fh:
            joblib.dump(self, fh)  
                  
    
    def _get_proxies(url):
        """
        Function meant to provide different proxies 
        to scrape the website of the url provided as input.
        """
        
        try:
            r_obj = requests.get(url)
        except:
            proxy = 0
            while not type(proxy) == str:
                
                try:
                    url = 'https://free-proxy-list.net/'
                    response = requests.get(url)
                    parser = fromstring(response.text)
                    ip = random.choice(parser.xpath('//tbody/tr'))
                    if ip.xpath('.//td[7][contains(text(),"yes")]'):
                        proxy = ":".join([ip.xpath('.//td[1]/text()')[0], ip.xpath('.//td[2]/text()')[0]])
                        proxies = {"http": proxy, "https": proxy}
                        
                except:
                   continue
       
            r_obj = requests.get(url, proxies)
                   
        return r_obj
    
    
    def _looper(x, function, **kwargs):
        """
        Wrapper function to apply the function passed as input to the list of words x 
        and return a regular expression with all the different ways in which
        all the words of the list can appear written in text, 
        given their shared morphology.
        """
        pattern_list = []
        for a in x:
            pattern = function(a, **kwargs)
            pattern_list.append(pattern)
        return "({0})".format('|'.join(pattern_list))
    
                
    def _verbal_regulater(a, irr_vbs):
        """
        Function to turn a verbal infinitive into a regular expression pattern 
        that matches all the declinations of that verb.
        
        Parameters:
            a (str): Verbal infinitive.
            irr_vbs (dict): Dictionary of irregular verbs with the infinitives as keys 
                and the declinations joined in a regular expression string as values.
            
        Returns:
            pattern (str): Not yet compiled regular expression pattern with 
                all the variant declinations of the verb passed as input. 
        """
        
        if regex.search(r'\s', a):
            first_word = a.split()[0]
            rest = regex.escape(' ' + ' '.join(a.split()[1:]))
        else:
            first_word = a
            rest = ''
            
        if first_word in irr_vbs:
            pattern = irr_vbs.get(first_word) + rest
        else:
            if regex.search(r'ie$', first_word):
                pattern = first_word.rstrip('ie') + '(ie|ied|ying|ies)' + rest
            elif regex.search(r'e$', first_word):
                pattern = first_word.rstrip('e') + '(e|ed|ing|es)' + rest
            elif regex.search(r'y$', first_word):
                pattern = first_word.rstrip('y') + '(y|ied|ying|ies|yed|ys)' + rest
            else:
                pattern = first_word + first_word[-1] + '?' + '(ed|ing|s)?' + rest 
                
        return pattern
    
    
    def _adject_regulater(a):
        """
        Function to turn an adjective into a regular expression pattern 
        that matches all the variant inflected forms of that adjective.
        
        Parameters:
            a (str): Adjective.
            
        Returns:
            pattern (str): Not yet compiled regular expression pattern with 
                all the variant inflected forms of the adjective passed as input. 
        """
        
        if regex.search(r'y$', a):
            pattern = regex.escape(a.rstrip('y')) + '(y|iest|ier)'
        elif len(a) <= 6:
            pattern = regex.escape(a) + '(st|r|er|est)?'            
        else:
            pattern = regex.escape(a)
        
        return pattern
    
    
    def _noun_regulater(a):
        """
        Function to turn a common noun into a regular expression pattern 
        that matches all the variant inflected forms of that noun.
        
        Parameters:
            a (str): Noun in singular form.
            
        Returns:
            pattern (str): Not yet compiled regular expression pattern with 
                all the variant inflected forms of the noun passed as input. 
        """
            
        if regex.search(r'[^aeiou]y$', a):
            pattern = a.rstrip('y') + '(y|ies)'
        elif re.search(r'[^aeiou]f$', a):
            if re.search(r'ff$', a):
                pattern = a.rstrip('f') + '(ff|ves)'
            else:
                pattern = a.rstrip('f') + '(f|ves)'
        elif re.search(r'[^aeiou]fe$', a):
            pattern = a.rstrip('fe') + '(fe|ves)'
        elif re.search(r'[^aeiou][aeiou]f$', a):
            pattern = a.rstrip('f') + '(f|ves)'
        elif re.search(r'[^aeiou][aeiou]fe$', a):
            pattern = a.rstrip('fe') + '(fe|ves)'
        elif re.search(r'^(wo)?man$', a):
            pattern = a.rstrip('man') + '(man|men)'
        elif re.search(r'^child$', a):
            pattern = '(child|children)'
        elif re.search(r'^foot$', a):
            pattern = '(foot|feet)'
        else:
            pattern = a + '(s|es)?'
    
        return pattern
    
    
    def _alternatives_disassembler(x):
        """
        Function to split up the different ways in which collocations that can be considered 
        semantically equivalent appear written, so that they become different entries.
        
        Parameters:
            x (str): The alternatives to a word or string of words split with a forward slash 
                and embedded in a longer phrase.
            
        Returns:
            b (list): List of strings, each with one of the alternatives that could previously 
                be found separated by a forward slash in the same string.
        """
         
        b = []
        for a in x:
            r = regex.search(r'\/', a)
            if r:
                a = regex.sub(r'(?<=\ban?)\s(?=\w+)', '_', a)
                for match in regex.findall(r'([\w\-\_]+\/[\w\-\_]+)', a):
                    for c in match.split("/"):
                        b.append(regex.sub(r'(?<=\ban?)_(?=\w+)', ' ', regex.sub(r"(?<=[\W_,])"+f"({match})"+"(?=[\W_,])", c, a)))
            else:
                b.append(a)
        return b
                    
              
    def _alts_diss(x):
        """
        Function to split up the different ways in which collocations that can be considered 
        semantically equivalent appear written, so that they become different entries.
        
        This function extends "alternatives_disassembler", in that it guarantees that strings 
        with several words separated by forward slashes can be split into as many strings as 
        the number of alternatives it featured.
        
        Parameters:
            x (str/list): The alternatives to a word or string of words split with a forward slash 
                and embedded in a longer phrase.
            
        Returns:
            x (list): List of strings, each with one of the alternatives that could previously 
                be found separated by a forward slash in the same string.
        """
        
        if not isinstance(x, list):
            x = [x]
        
        while regex.search(r'\/', '; '.join(x)):
            x = list(set(Collocater._alternatives_disassembler(x)))  
    
        return x
    
    
    def _cleaner(x, tags_dict):
        """
        Function to clean the scraped non-cursive content of 
        the Online Oxford Collocation Dictionary's pages.
        
        Parameters:
            x (str): Raw content
            tags_dict (dict): Python dictionary to replace the references to pronouns 
                and other non-set discoursive variables that don't refer to 
                collocations with traceable tags.
        """
        
        return regex.sub(r'Special\spage\sat', '', 
                         regex.sub(r'(\(.?\=[^\)]+\))|(,\setc)', '', 
                                  regex.sub(r'(?<=\w+)(,\s)(?=\w+,\setc\s'+f"{tags_dict.get('this_word')})", '/',
                                            regex.sub(regex.compile(tags_dict.get('this_word') + '|' + '~', regex.I), tags_dict.get('this_word'),
                                                      regex.sub(r'…', tags_dict.get('one_word'),
                                                                regex.sub(r"(?<=\W)(your|his|her|their|my|our|("+f"{tags_dict.get('someone')}"+"|"+f"{tags_dict.get('sb_sth')}"+"|"+f"{tags_dict.get('something')}"+ "|a\sperson|one)'s)(?=\W)", tags_dict.get('possessive_det'),
                                                                          regex.sub(r"(?<=\W)(some(one|body)|sb|you|him|her|them|us|we|they|he|she)(?=\W)", tags_dict.get('someone'),
                                                                                    regex.sub(r"(?<=\W)((some|a)?things?|sth)(?=\W)", tags_dict.get('something'),
                                                                                              regex.sub(r"(?<=\W)(some(one|body)\/something|sb\/sth)(?=\W)", tags_dict.get('sb_sth'),
                                                                                                        regex.sub(r'[A-Z]{2,}', '', 
                                                                                                                  regex.sub(r'([\<\>\.\+]|\&\w+)', '', 
                                                                                                                            regex.sub(r'\([^\)]{23,}\)', '', 
                                                                                                                                     regex.sub(r'<.?\w>', '', ' '+ x + ' ')))))))))))))
    
        
    def _colls_processor(without_examples, tags_dict):
        """
        Function to process the raw content retrieved from the Online Oxford Dictionary's 
        entries and return a list with all the collocations of each unique combination 
        of the word's different senses and the collocations' morphologies. 
        
        Parameters:
            without_examples (str): Raw content, bereft of the cursive strings, 
                which stand for the examples given for each collocation.
            tags_dict (dict): Python dictionary to replace the references to pronouns 
                and other non-set discoursive variables that don't refer to 
                collocations with traceable tags.
            
        Returns:
            singletons (list): All the collocations of the same morphology 
                for each of the word's senses. 
        """
        
        cleaned_colls = Collocater._cleaner(without_examples, tags_dict)
        dissambled_colls0 = '; '.join(Collocater._alts_diss(cleaned_colls))
        
        if regex.search(r'[\(\)]+', dissambled_colls0):
            dissambled_colls = regex.sub(r'[\(\)]+', '', regex.sub(r'\([\w\s\-]+\)', '', dissambled_colls0))
            dissambled_colls += '; '+regex.sub(r'[\(\)]+', '', dissambled_colls0)
        else:
            dissambled_colls = dissambled_colls0
                
        singles = [e for e in list(map(lambda x: x.strip(), regex.split(r'[,;\:\.\|]', regex.sub(r'(\S+\s)(?=\1)', '', regex.sub(r'\s+', ' ', dissambled_colls))))) 
        if not (regex.search(r'[\/\(]', e) or regex.match(r"({0})$".format(tags_dict.get('this_word')), e))]
        singletons = list(set([e for e in singles if e]))
        
        return singletons
    
        
    def collocate(self, word, verbose=False):
        """
        Scrapes the Online Oxford Collocation Dictionary to extract collocations.
        
        Parameters:
            word (str): The word to be queried in the Online Oxford Collocation Dictionary.
            verbose (bool): Optional argument to print message out to screen when collocations 
                could not be found for the word provided as input.
            
        Returns:
            collocations (dict): All the collocations for the word provided as input, 
                sorted according to their morphologies and the senses
                the queried word has when they are found acting as the word's collocations.
        """
        
        if word in self.collocations_dictionary:
            return self.collocations_dictionary.get(word)

        url0 = 'http://oxforddictionary.so8848.com/search?word='
        ox_coll = Collocater._get_proxies(url0 + word)
        core_soup = bs(ox_coll.text, 'lxml')  
          
        try:
            soup = core_soup.find_all('div', {'class':'item'})
                
        except:
            soup = [core_soup.find('div', {'class':'item'})]
            
        if soup:
            word_type = []
            for s in soup:
                try:
                    word_type.append(s.find_all('p', {'class':'word'}))
                except:
                    word_type.append([s.find('p', {'class':'word'})])
            word_type = sum(word_type, [])
        else:
            if verbose:
                print(f"""
                      No collocations found for '{word}', sorry. 
                      Try with a different word!
                      """)
            return None
        
        tags_dict = self.tags_dict
        tags_dict['this_word'] = word
    
        collocations = {}
        for idx in range(len(word_type)):
            if not word_type[idx].i:
                continue
            wt = word_type[idx].i.string.strip()
            collocations[wt] = {}
            for a in soup[idx].find_all('p'):
                if a.u:
                    word_morph = a.u.string.strip()  
                    word_morph = regex.sub(regex.compile('(\w+\,\s)*'+ word + '(\,\s\w+)*', regex.I), tags_dict.get('this_word'), word_morph)
                else:
                    continue
                    
                try:
                    examples = a.find_all('i')
                    re_examples = regex.compile('|'.join(list(map(lambda x: regex.escape(str(x)), examples))))
                    without_examples = regex.sub(re_examples, '', str(a))
    
                except:
                    without_examples = str(a)
                                    
                if word == 'look' and word_morph == 'PREP.':
                    if regex.search(r'glazed', without_examples):
                        without_examples0, without_examples = regex.split(r'.(?=<b>glazed)',  without_examples)
                        collocations[wt].setdefault(word_morph, []).append(Collocater._colls_processor(without_examples0, tags_dict))
                        word_morph = 'ADJ.'
                        
                singletons = Collocater._colls_processor(without_examples, tags_dict)
                collocations[wt].setdefault(word_morph, []).append(singletons)   
                
        self.collocations_dictionary[word] = collocations
        
        return collocations
    
    
    def collocations_identifier(self, word, morpho, text):
        """
        Function to build and compile the regular expressions to match 
        the collocations of nouns or verbs in text and return them.
        
        Parameters:
            word (str): The word for which collocations should be identified.
            morpho (string): The inputted word's morphology, which takes on the values 
                of either 'noun' or 'verb'.
            text (str): The text where collocations should be found.
                
        Returns:
            coll_matches (dict): All the matches for the inputted word's collocations 
                in the inputted text, sorted according to their morphologies, 
                given the word's morphology.
        """
    
        collocations = self.collocate(word)
        
        if not collocations:
            return {}
        
        tags_dict = self.tags_dict
        tags_dict['this_word'] = word
    
        text = regex.sub(r"\band\b", '&&', regex.sub(r"\bor\b", "@@", text))
    
        if morpho == 'noun' and collocations.get('noun'):
            word1 = Collocater._noun_regulater(word)
            adv = ''
    
            if collocations.get('noun').get('ADJ.'):
                a = list(set(sum(collocations.get('noun').get('ADJ.'), [])))
                b = Collocater._looper(a, Collocater._adject_regulater)
                adj = (f"(({b})\s(([n\&\@]+|yet)\s({b})\s)?{word1}"+ ')|(' +
                       f"{word1}" + 
                       r"\s((is|was|were)(\s[\w]+ing)?|look(s|ed)|(seem(s|ed)|appear(s|ed))(\sto\sbe)?)(\s[\w\-]+)?\s" + 
                       f"({b})(\s([\&\@]+|yet)\s({b}))?)")
            else:
                adj = ''
                
            if collocations.get('noun').get('VERB + '+tags_dict.get('this_word')):
                a = set(sum(collocations.get('noun').get('VERB + '+tags_dict.get('this_word')), []))
                b = [e for e in a if not e in ['have', 'be']]
                if b:
                    c = Collocater._looper(b, Collocater._verbal_regulater, irr_vbs=self.irr_verbs)
                    d = regex.sub(r'(\\ )?__[A-Z_]+__', '', c)
                    e = regex.sub(r'(?<=\()\||\|(?=\))', '', regex.sub(r'\|+', '|', 
                                  regex.sub(r'((?<=|)(ing|\w+ing))', '', d)))
                    
                    relevant_preps = set(regex.findall(r'(?<=\s)[a-z]+(?=_)', '_'.join(a)))
                    prepositions0 = [p for p in self.prepositions if not p in relevant_preps]
                    prep_re1 = '|'.join(self.prepositions)
                    prep_re = '|'.join(prepositions0)
                    
                    pre_verb = (f"(({c})" + r"(\s(?!(?:(" + f'{prep_re}' + r")\s))[\w\*\-\']+){0,3}\s" + f"{word1}" + ')|(' +
                                f"{word1}" + r"(\s(?!(?:(" + f'{prep_re1}' + r")\s))[\w\*\-\']+){0,5}\s" + f"({e})"+ ')|(' +
                                f"{word1}" + r"(\s(?!(?:(" + f'{prep_re1}' + r")\s))[\w\*\-\']+){1,4}\s" +
                                r"((is|was|were|been)(\s\w+ing\s" + f'({prep_re1})' + r")?|to\sbe)\s" + 
                                f"({d}))")
                else:
                    pre_verb = ''
            else:
                pre_verb = ''
                
            if collocations.get('noun').get(tags_dict.get('this_word')+' + VERB'):
                a = set(sum(collocations.get('noun').get(tags_dict.get('this_word')+' + VERB'), []))
                b = [e for e in a if not e in ['have', 'be']]
                if b:
                    c = Collocater._looper(b, Collocater._verbal_regulater, irr_vbs=self.irr_verbs)
                                
                    relevant_preps = set(regex.findall(r'(?<=\s)[a-z]+(?=_)', '_'.join(a)))
                    prepositions0 = [p for p in self.prepositions if not p in relevant_preps]
                    prep_re = '|'.join(prepositions0)
                    
                    post_verb = f"{word1}"  + r"(\s(?!(?:(" + f'{prep_re}' + r")\s))[\w\*\-\']+){0,3}\s" + f"({c})"
                else:
                    post_verb = ''
            else:
                post_verb = ''
    
            if collocations.get('noun').get(tags_dict.get('this_word')+' + NOUN'):
                a = list(set(sum(collocations.get('noun').get(tags_dict.get('this_word')+' + NOUN'), [])))
                b = Collocater._looper(a, Collocater._noun_regulater)
                post_noun = f"{word1}\s" + f"({b})"
            else:
                post_noun = ''
    
            if collocations.get('noun').get('QUANT.'):
                a = list(set(sum(collocations.get('noun').get('QUANT.'), [])))
                b = Collocater._looper(a, Collocater._noun_regulater)
                quant = f"({b})" + r"\sof\s([\w\*\-\']+\s){0,2}"  + f"{word1}"
            else:
                quant = ''
                
            if collocations.get('noun').get('PREP.'):
                a = list(set(sum(collocations.get('noun').get('PREP.'), [])))
                prep = "{0}".format('|'.join(list(map(regex.escape, a))))
            else:
                prep = ''
                
            if collocations.get('noun').get('PHRASES'):
                a = sum(collocations.get('noun').get('PHRASES'), [])
                phr = "{0}".format('|'.join(list(map(regex.escape, a))))
            else:
                phr = ''
                
        elif morpho == 'verb' and collocations.get('verb'):
            word1 = Collocater._verbal_regulater(word, irr_vbs=self.irr_verbs)
            adj, post_verb, post_noun, quant = '', '', '', ''
    
            if collocations.get('verb').get('PREP.'):
                a = list(set(sum(collocations.get('verb').get('PREP.'), [])))
                prep = f"{word1}"  + r"(\s[\w\*\-]+){0,1}\s" + "({0})".format('|'.join(list(map(regex.escape, a))))
            else:
                prep = ''
                
            if collocations.get('verb').get('ADV.'):
                a = list(set(sum(collocations.get('verb').get('ADV.'), [])))
                b = [e for e in a if not (e == 'well' or len(e) <= 3)]
                if b:
                    adv = (f"{word1}" + r"(\s[\w\*\-\'\&\@]+){0,3}\s" +
                           "({0})|({1})".format('|'.join(list(map(regex.escape, a))), '|'.join(list(map(regex.escape, b)))) + 
                           r"(\s[\w\*\-\'\&\@]+){0,3}\s" + f"{word1}")
                else:
                    adv = ''
            else:
                adv = ''  
            
            if collocations.get('verb').get('PHRASES'):
                a = sum(collocations.get('verb').get('PHRASES'), [])
                phr = "{0}".format('|'.join(list(map(lambda x: regex.sub(regex.compile(word), word1, regex.escape(x)), a))))
            else:
                phr = ''
                
            if collocations.get('verb').get('VERB + '+tags_dict.get('this_word')):
                a = list(set(sum(collocations.get('verb').get('VERB + '+tags_dict.get('this_word')), [])))
                b = Collocater._looper(a, Collocater._verbal_regulater, irr_vbs=self.irr_verbs)
                            
                relevant_preps = set(regex.findall(r'(?<=\s)[a-z]+(?=_)', '_'.join(a)))
                prepositions0 = [p for p in self.prepositions if not p in relevant_preps]
                prep_re = '|'.join(prepositions0)
                
                pre_verb = f"({b})" + r"(\s(?!(?:(" + f'{prep_re}' + r")\s))[\w\*\-\&\@\']+){0,3}\s" + f"{word1}"
            else:
                pre_verb = '' 
        else:
            adj, pre_verb, post_verb, post_noun, quant, prep, adv, phr = '', '', '', '', '', '', '', ''
            
            
        colls_types = {'adj': adj, 'pre_verb': pre_verb, 
                       'post_verb': post_verb, 'post_noun': post_noun, 
                       'quant': quant, 'prep': prep, 'phr': phr, 'adv': adv}
                
    
        if not self.chosen_collocation_types:
            self.collocations_types = colls_types
        else:
            self.collocations_types = {k:v for k, v in colls_types.items() if k in self.chosen_collocation_types}
        
        
        coll_matches = {}
        for key, reg in self.collocations_types.items():
            
            if reg:
                string1 = f"((?:[\W_]|^)({reg})(?:[\W_]|$))"
                string2 = regex.sub(r'(?<!\{)\d+(?!\})', '\d+', string1)
                string3 = regex.sub(r'((\\ )?__[A-Z]+__)(?=\\ )', "(\s[\w\-]+){1,3}", string2)
                string4 = regex.sub(r'((\\ )?__[A-Z_]+__)(?=\\ )', "(\s((his|her|their|our|my|your)(\s[\w\-]+){0,2}|([\w\-\.]+\s)?[\w\-]+\'s?))", string3)
                string5 = regex.sub(r'((\\ )?__[A-Z_]+__)', "(\s((the|an?|this|that|these|those|his|her|their|our|my|your|some|many|few|plenty)\s)?[\w\*\-\']+)", string4)
                pattern1 = regex.compile(string5, regex.I)
                all_colls1 = regex.findall(pattern1, text)
        
                relevant_matches = [a for a in sum(all_colls1, ()) if a]
                if all_colls1 and relevant_matches:
                    collocated0 = [[regex.sub(r'(^\W*|\W*$)', '', regex.sub(r"\&\&", 'and', regex.sub(r"\@\@", "or", a))) 
                    for a in e if a and regex.search(r'\b'+word1+r'\b', a, regex.I)] for e in all_colls1]
                    if sum(collocated0, []):
                        collocated = [elem[0] for elem in collocated0 if elem]
                        coll_matches[key] = collocated
                    
        return coll_matches
                
    
    def __call__(self, doc):
        """
        Retrieves, from the type of collocations it's instructed to look for,
        the collocations that could be found for either verbs, 
        nouns or both in the inputted text, and returns either a dictionary
        with the collocations found in the text or the text parsed by Spacy 
        with its added collocations finder component.
        
        Parameters:
            doc (str/spacy.tokens.doc.Doc): The text whose collocations are meant to be found.
                
        Returns:
            when the input is a spacy.tokens.doc.Doc:
                doc (spacy.tokens.doc.Doc): The inputted text with the collocations 
                    found in them added to them in the token and span level of 
                    Spacy's added component.
            when the input is a string:
                found_colls_dict (dict): Python dictionary with the collocations found as keys, 
                    and, as values, the positions of their first and last tokens and 
                    the morphology of both of the collocations' word component 
        """
        
        nlp = spacy.load(self.spacy_model, disable=['ner'])

        if isinstance(doc, str):
            doc = nlp(doc)
            orig_format = 'string'
        elif isinstance(doc, spacy.tokens.doc.Doc):
            orig_format = 'spacy_doc'
        else:
            raise ValueError("The inputted text must either be a string or a spacy.tokens.doc.Doc object") 
            
            
        if self.chosen_word_types == 'both':
            lookups0 = [{i: (t.orth_, t.lemma_, t.pos_.lower())} for i, t in enumerate(doc) if t.pos_ in ['NOUN','VERB']]
        else:
            lookups0 = [{i: (t.orth_, t.lemma_, t.pos_.lower())} for i, t in enumerate(doc) if t.pos_ == self.chosen_word_types.upper()]

        lookups = {k: v for d in lookups0 for k, v in d.items()}

        doc[0].set_extension('colloc', force=True, default={})
        doc.set_extension('collocs', force=True, default=[])
        
        matcher = PhraseMatcher(doc.vocab)

        labels = {}
        for idx, combi in lookups.items():
            tok, lemma, morpho = combi
            colls_in_text = self.collocations_identifier(str(lemma), str(morpho), str(doc))
            if colls_in_text:
                patch = str(doc[max(idx-7, 0): min(idx+9, len(doc)-1)])
                all_this_wrd_colls = sum(colls_in_text.values(), [])
                this_match = [val for val in all_this_wrd_colls if regex.search(regex.compile(regex.escape(val), regex.I), patch)]
                if this_match:
                    this_colls = {}
                    for k, v in colls_in_text.items():
                        interin = set(this_match).intersection(set(v))
                        if interin:
                            e = 0
                            for rule_name in interin:
                                matcher.add('_'.join([lemma, morpho, k, str(e)]), None, nlp(rule_name))
                                labels.setdefault(rule_name, []).append('{0}_{1}__{2}'.format(lemma, morpho, k))
                                e += 1
                            this_colls[k] = list(interin)
                            doc[idx]._.colloc = this_colls

        spans = []
        idx = 0
        found_colls_dict = {}
        for _, start, end in matcher(doc):
            key = str(doc[start:end])
            my_label = ' / '.join(set(labels.get(key)))
            spans.append(Span(doc, start, end, label=my_label))
            found_colls_dict.setdefault(key, []).append({'coll_type': my_label, 'location': [start, end]})
        
        doc._.collocs = spans
        
        if orig_format == 'string':
            found_colls_dict = {key: {k: v for d in val for k, v in d.items()} 
            for key, val in found_colls_dict.items()}
            return found_colls_dict
        
        else:
            return doc
    
    


