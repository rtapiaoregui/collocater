#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 17:21:07 2020

@author: rita
"""


from collocater import collocater

import joblib
import spacy


import os
from random import choice
from pprint import pprint

if __name__ == '__main__':
    
    
    data_path = os.path.join(os.path.dirname(__file__), 'data')
    entire_class_path = os.path.join(data_path, 'collocater_obj.joblib')
    prep_path = os.path.join(data_path, 'prepositions.joblib')
    irr_verbs_path = os.path.join(data_path, 'irr_verbs_dict.joblib')
    colls_dict_path = os.path.join(data_path, 'collocations_dict.joblib')

    spacy_model = 'en_core_web_sm'
    
    examples = {'eye': """The dog's hungry eyes were on my sandwich. 
                He screwed up his dark eyes against the glare of the sun. 
                An eye for an eye, that's what the Bible says. He warily eyed at her, though still in awe.
                I want you under my eye at all times and not just wandering around in dark alleys
                Keep an eye on him, he has been eyeing your daughter for a while. 
                He held up the newspaper to shield his eyes from the sun.""",
                'string': "I'd rather have a tight figure than to be dangling on a fdg-fdf xgnf string.",
                'end': """This feels like the end of an era. 
                The story was brought to a sharp end. If you were to ask me it always has tragically been ending in madness. 
                I feel like this is bound to end in disaster.
                The money could have been used to more beneficial ends. This ends here, what a scam!
                She wished to have a house built, and to this end she engaged a local architect.""",
                'flower': """If this isn't a bunch of beautiful flowers I don't know what is!""",
                'time': """If someone were to ask me, I would have to agree that there is no time like 
                the Greenwich Mean time to be alive, however strange that may sound.""", 
                'thumb': """Peter is kind of a weirdo, he sticks out like a sore thumb in any crowd.""",
                'house': "The house lies on the top of a mountain.",
                'special': "There are lots of TV Christmas specials for children this year. Can someone tell me what's the daily special?",
                'bridge': """The road goes under the old railway bridge. 
                The new bridge will cross the Thames at this crucial point in time in our ordinary lives.""",
                'actor': "The child actor was cast in a movie about relationships in the Mid West.",
                'actress': "She was one of many experienced actresses who auditioned for the part of Hamlet.", 
                'sacrifice': "She was prepared to sacrifice having a family in order to pursue her bad and glittering career.",
                'coffee': "A smell of coffee is the most delightful thing I can possibly imagine.",
                'party': """Now that can mean either China's top leaders are partly at fault; 
                or the Communist Party's governance structures need to be overhauled.""", 
                'position': "Soft laughter ran through the crowd as the people stirred back into position after Mrs. Hutchinson’s arrival.",
                'idea': "I love this idea you've come up with.",
                'problem': "Success brings its own problems. Staff shortages cause problems for the organization.",
                'look': """That look seems hella serious. His careful look and critical gaze. He looked at her with contempt. 
                We had a good look around the old town.
                It looks to me as if the company is in real trouble. She looked towards the door. 
                He gave me a funny look. """, 
                'weight': "This plank had been held in place by the weight of the captain", 
                'go': "You may as well go book your next holidays in a lovely wristband resort right away!", 
                'path': """Well, we are here to free you of that burden and show you the path to making an honorable living, 
                without the need to resort to haggling for a measly income.""", 
                'tale': """the characters of the One-Thousand-and-One-Night tales they know they are being regaled with to lose 
                sense of what material goods cost.""",
                'year': "I alloted all my year spending budget on shoes.",
                'day': "The day they had been thinking of spending by the sun-drenched and secluded beach. The day they so desperately wanted to be spending by the beach.", 
                'view': "He enjoyed a view like no other, one only gods ought to enjoy, and it had now become his tall yet narrow window to the outside world.",
                'convert': "He tried to convert him from paganism to Catholicism."
                }
                
    shorter_out = True
    
    nlp = spacy.load(spacy_model)

    try:
        collie = collocater.Collocater.loader(entire_class_path)
    except:
        with open(irr_verbs_path, 'rb') as fh:
            irr_verbs = joblib.load(fh)
            
        with open(prep_path, 'rb') as fh:
            prepositions = joblib.load(fh)

        with open(colls_dict_path, 'rb') as fh:
            collocations_dictionary = joblib.load(fh)
            
        collie = collocater.Collocater(irr_verbs, prepositions, 
                            collocations_dictionary=collocations_dictionary)


    if shorter_out:
        rand_key = choice(list(examples.keys()))
        text = examples.get(rand_key)
    else:
        text = ' '.join(examples.values())


    doc = nlp(text)
    wrong_doc = False
    
    found_collocations = collie(text)
    found_collocations1 = collie(nlp(text))
    
    print(f"\nOutput of collie(text) with text as a str:\n")
    pprint(found_collocations)
    
    if found_collocations:
        colls_df = collocater.store_collocs_in_df(found_collocations)
        print(f"\nFirst row of the dataframe with all collocations found:\n")
        print(colls_df.iloc[0])
        
    print("\n\nTokens with associated collocations:\n")
    pprint([(col.orth_, col._.colloc) for col in found_collocations1 if col._.colloc])
    
    print("\n\nTokens with associated collocations in text:\n")
    colls = [(col.text, col.start_char, col.end_char, col.label_) for col in found_collocations1._.collocs]
    pprint(colls)
    
    print("\n\nList of all the collocations found:\n")
    print(found_collocations1._.collocs)
    
    collie.saver(entire_class_path)

    
    
    