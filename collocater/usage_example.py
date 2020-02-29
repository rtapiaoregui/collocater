#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 29 17:35:03 2020

@author: rita
"""

from collocater import collocater
import spacy

collie = collocater.Collocater.loader()
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe(collie)
print(nlp.pipe_names)

text = 'The sky is blue, despite the grass being green.'
doc = nlp(text)
print(doc._.collocs)