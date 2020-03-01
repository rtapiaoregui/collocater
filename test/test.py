#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 10:21:27 2020

@author: rita
"""

import pytest, os
import regex
from collocater.collocater import Collocater, store_collocs_in_df
import spacy




@pytest.fixture
def test_datafinder():
    
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
    
    data_pack = {'spacy_model': spacy_model, 
                 'examples': examples, 
                 'word': 'eye'}
    
    return data_pack



@pytest.fixture
def test_loader(test_datafinder):
    collie = Collocater.loader()
    
    return collie


@pytest.fixture
def test_collocater_out(test_datafinder, test_loader):
    
    text = ' '.join(test_datafinder.get('examples').values())
    assert type(text) == str
    found_collocations = test_loader(text)
    
    with pytest.raises(ValueError):
        test_loader(None)
            
    nlp = spacy.load(test_datafinder.get('spacy_model'))
    
    if 'colls' in nlp.pipe_names:
        nlp.remove_pipe('colls')
        
    assert not 'colls' in nlp.pipe_names
    
    doc = nlp(text)
    
    doc_direct_output = test_loader(doc)        

    nlp.add_pipe(test_loader)
    
    assert 'colls' in nlp.pipe_names
    
    doc_with_enriched_pipe = nlp(text)
    
    output = {'found_collocations': found_collocations, 
             'spacy_colls_via_collocater': doc_direct_output, 
             'spacy_colls_via_nlp': doc_with_enriched_pipe
             }
    
    return output


def test_collocater_obj(test_loader):
    
    assert isinstance(test_loader.irr_verbs, dict)
    assert isinstance(test_loader.prepositions, list)
    assert isinstance(test_loader.collocations_dictionary, dict)
    

def test_collocater(test_datafinder, test_loader):
        
    collocations = test_loader.collocate(test_datafinder.get('word'))

    assert list(collocations.keys())[-1] == 'verb'
    assert len(collocations.get('noun').get('ADJ.')) == 3
    assert 'blue'  in sum(collocations.get('noun').get('ADJ.'), [])
    assert 'brown' in sum(collocations.get('noun').get('ADJ.'), [])
    assert 'dark' in sum(collocations.get('noun').get('ADJ.'), [])
    assert 'swollen' in sum(collocations.get('noun').get('ADJ.'), [])
    assert 'look __PERSON__ straight in' in sum(collocations.get('noun').get('VERB + ' + 'eye'), [])
    assert 'dwell on __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    assert 'fasten on __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    assert 'be riveted on __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    assert 'be riveted to __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    assert 'raise __PERSON_S__ eyes heavenwards' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'with the naked eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'with the unaided eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'to the unaided eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'to the naked eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'under __PERSON_S__ critical eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'under __PERSON_S__ watchful eye' in sum(collocations.get('noun').get('PHRASES'), [])
    assert "in __PERSON_S__ mind's eye" in sum(collocations.get('noun').get('PHRASES'), [])
    assert 'gaze up at __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    assert 'gaze at __OTHER__' in sum(collocations.get('noun').get('eye' + ' + VERB'), [])
    
   
def test_collocations_identifier(test_datafinder, test_loader):
    
    coll_matches =  test_loader.collocations_identifier(test_datafinder.get('word'), 'noun', 
                                                        test_datafinder.get('examples').get(test_datafinder.get('word')))
    
    assert len(coll_matches.get('adj')) == 2
    assert len(coll_matches.get('pre_verb')) == 2
    assert len(coll_matches.get('prep')) == 2
    assert len(coll_matches.get('phr')) == 1
    assert 'Keep an eye on him' in coll_matches.get('phr')
    assert 'screwed up his dark eyes' in coll_matches.get('pre_verb')
    assert 'dark eyes' in coll_matches.get('adj')
    assert 'hungry eyes' in coll_matches.get('adj')
    assert 'under my eye' in coll_matches.get('prep')
    
    

def test_found_colls_in_text(test_collocater_out):
    
    found_collocations = test_collocater_out.get('found_collocations')
    
    assert found_collocations.get('dark alleys').get('coll_type') == 'alley_noun__adj'
    assert found_collocations.get('hungry eyes').get('coll_type') == 'eye_noun__adj'
    assert found_collocations.get('dark eyes').get('coll_type') == 'eye_noun__adj'
    assert found_collocations.get('screwed up his dark eyes').get('coll_type') == 'eye_noun__pre_verb'
    assert found_collocations.get('under my eye').get('coll_type') == 'eye_noun__prep'
    assert found_collocations.get('eye for').get('coll_type') == 'eye_noun__prep'
    assert found_collocations.get('warily eyed').get('coll_type') == 'eye_verb__adv'
    assert found_collocations.get('beautiful flowers').get('coll_type') == 'flower_noun__adj'
    assert found_collocations.get('bunch of beautiful flowers').get('coll_type') == 'flower_noun__quant'
    assert found_collocations.get('against the glare').get('coll_type') == 'glare_noun__prep'
    assert found_collocations.get('eye for').get('coll_type') == 'eye_noun__prep'
    assert found_collocations.get('Greenwich Mean time').get('coll_type') == 'time_noun__adj'
    assert regex.search(r'era_noun__phr', found_collocations.get('the end of an era').get('coll_type'))
    assert regex.search(r'end_noun__phr', found_collocations.get('the end of an era').get('coll_type'))
    assert regex.search(r'disaster_noun__pre_verb', found_collocations.get('end in disaster').get('coll_type'))
    assert regex.search(r'end_verb__phr', found_collocations.get('end in disaster').get('coll_type'))
    assert found_collocations.get('ending in').get('coll_type') == 'end_verb__prep'
    assert found_collocations.get('bound to').get('coll_type') == 'bind_verb__prep'
    assert found_collocations.get('Keep an eye on him').get('coll_type') == 'eye_noun__phr'
    assert found_collocations.get('brought to a sharp end').get('coll_type') == 'end_noun__pre_verb'
    assert found_collocations.get('tragically been ending').get('coll_type') == 'end_verb__adv'
    assert found_collocations.get('bridge will cross the Thames').get('coll_type') == 'bridge_noun__post_verb'
    assert found_collocations.get('crucial point').get('coll_type') == 'point_noun__adj'
    assert found_collocations.get('point in').get('coll_type') == 'point_noun__prep'
    assert found_collocations.get('in time').get('coll_type') == 'time_noun__prep'
    assert found_collocations.get('ordinary lives').get('coll_type') == 'life_noun__adj'
    assert found_collocations.get('daily special').get('coll_type') == 'special_noun__adj'
    assert regex.search(r'child_noun__post_noun', found_collocations.get('child actor').get('coll_type'))
    assert regex.search(r'actor_noun__adj', found_collocations.get('child actor').get('coll_type'))
    assert found_collocations.get('actor was cast').get('coll_type') == 'actor_noun__pre_verb'
    assert found_collocations.get('experienced actresses').get('coll_type') == 'actress_noun__adj'
    assert regex.search(r'actress_noun__pre_verb', found_collocations.get('actresses who auditioned').get('coll_type'))
    assert regex.search(r'actress_noun__post_verb', found_collocations.get('actresses who auditioned').get('coll_type'))
    assert found_collocations.get('was prepared to sacrifice').get('coll_type') == 'sacrifice_verb__pre_verb'
    assert found_collocations.get('A smell of coffee').get('coll_type') == 'coffee_noun__phr'
    assert found_collocations.get('can possibly imagine').get('coll_type') == 'imagine_verb__pre_verb'
    assert found_collocations.get('into position').get('coll_type') == 'position_noun__prep'
    assert found_collocations.get("idea you've come up with").get('coll_type') == 'idea_noun__pre_verb'
    assert found_collocations.get("look seems hella serious").get('coll_type') == 'look_noun__adj'
    assert found_collocations.get("brings its own problems").get('coll_type') == 'problem_noun__pre_verb'
    assert found_collocations.get("cause problems").get('coll_type') == 'problem_noun__pre_verb'
    assert found_collocations.get("looked at").get('coll_type') == 'look_verb__prep'
    assert found_collocations.get("look around").get('coll_type') == 'look_noun__prep'
    assert not "place by the weight" in found_collocations
    assert not "year spending" in found_collocations
    assert not "path to making" in found_collocations
    assert found_collocations.get("tales they know they are being regaled with").get('coll_type') == 'tale_noun__pre_verb'
    assert found_collocations.get('day they had been thinking of spending').get('coll_type') == 'day_noun__pre_verb'
    assert found_collocations.get('day they so desperately wanted to be spending').get('coll_type') == 'day_noun__pre_verb'
    assert found_collocations.get('enjoyed a view').get('coll_type') == 'view_noun__pre_verb'
    assert found_collocations.get('sun-drenched and secluded beach').get('coll_type') == 'beach_noun__adj'
    assert found_collocations.get("tall yet narrow window").get('coll_type') == 'window_noun__adj'
    assert found_collocations.get("glittering career").get('coll_type') == 'career_noun__adj'
    assert not "bad and glittering career" in found_collocations
    
    
def test_spacy_colls_component(test_datafinder, test_collocater_out):
    
    for doc in [test_collocater_out.get('spacy_colls_via_collocater'), 
                test_collocater_out.get('spacy_colls_via_nlp')]:
    
        collocs_per_token = [(col.orth_, col._.colloc) for col in doc if col._.colloc]
        assert collocs_per_token
        assert collocs_per_token[0][0] == 'eyes' and collocs_per_token[1][0] == 'eyes'
        assert 'hungry eyes' in collocs_per_token[0][1].get('adj')
        assert 'screwed up his dark eyes' in collocs_per_token[1][1].get('pre_verb')
        assert 'against the glare' in collocs_per_token[2][1].get('prep')
        assert 'warily eyed' in collocs_per_token[5][1].get('adv')
        assert 'just wandering' in collocs_per_token[7][1].get('adv')
        assert 'wandering around' in collocs_per_token[7][1].get('prep')
        assert 'Keep an eye on him' in collocs_per_token[9][1].get('phr')
    
        colls = [(col.text, col.start_char, col.end_char, col.label_) for col in doc._.collocs]
        assert colls[0] == ('hungry eyes', 10, 21, 'eye_noun__adj')
        assert colls[10] == ('Keep an eye on him', 340, 358, 'eye_noun__phr')
        assert colls[20] == ('bound to', 756, 764, 'bind_verb__prep')
        assert colls[30] == ('beautiful flowers', 1005, 1022, 'flower_noun__adj')
       
       
    
def test_collocater_saver(test_datafinder, test_loader, tmp_path):
    
    path = os.path.join(tmp_path,'tmp.joblib')
    
    if os.path.exists(path):
        os.remove(path)

    test_loader.saver(path)

    assert os.path.exists(path)
    os.remove(path)


def test_store_in_df(test_collocater_out):
    
    found_collocations = test_collocater_out.get('found_collocations')

    df = store_collocs_in_df(found_collocations)
    
    assert df.shape == (98, 3)
    assert df.columns.tolist() == ['Morphology of word with collocation', 
                            'Type of collocation',
                            'Positions of first and last token of collocation']
    
    assert df.index[0] == 'hungry eyes'
    assert 'eye (noun)' in df.loc[:,["Morphology of word with collocation"]].iloc[0].tolist()
    assert 'Adjective' in df.loc[:,['Type of collocation']].iloc[0].tolist()
    assert 'start: 4; end: 5' in df.loc[:,['Positions of first and last token of collocation']].iloc[0].tolist()
    
    assert df.index[1] == 'screwed up his dark eyes'
    assert 'eye (noun)' in df.loc[:,["Morphology of word with collocation"]].iloc[1].tolist()
    assert 'Object of verb' in df.loc[:,['Type of collocation']].iloc[1].tolist()
    assert 'start: 13; end: 17' in df.loc[:,['Positions of first and last token of collocation']].iloc[1].tolist()
    
        
    