import numpy
import numpy as np
import pandas as pd
from django.contrib.auth.models import Group
from pythainlp import word_tokenize
from pythainlp.corpus import thai_stopwords, thai_words
from pythainlp.util import dict_trie
from rest_framework.response import Response
from rest_framework.views import APIView

from .apps import DocClassifyConfig

custom_trie = dict_trie(dict_source=DocClassifyConfig.DICT_FILE)
th_words = set(thai_words())
th_words.update(custom_trie)
th_word_trie = dict_trie(th_words)
stopwords = list(thai_stopwords())


def tokenize(title, unit):
    tokenized = word_tokenize(title.replace(',', "").replace('"', "").replace('/', ""), engine="newmm",
                              custom_dict=th_word_trie,
                              keep_whitespace=False)
    tokenized.append(unit)
    return [word for word in tokenized if word not in stopwords]


def vec_for_testing(model_dbow, topic, epochs):
    regressors = tuple([model_dbow.infer_vector(topic, epochs=epochs)])
    return regressors


class DocClassification(APIView):
    def post(self, request):
        data = request.data
        epochs = 20
        thresholds = 0.05
        unit = data['doc_unit']
        title = data['doc_title']
        classify_model = DocClassifyConfig.model
        d2v_model = DocClassifyConfig.d2v

        tokenized_title = tokenize(title, unit)
        regressor = vec_for_testing(d2v_model, tokenized_title, epochs)
        raw_received_units = classify_model.predict(regressor)
        classes = ['กกช.', 'กกร.', 'กคง.', 'กธก.(กพ.)', 'กธก.(บร.)', 'กธก.(สก.)',
       'กธก.(สบ.)', 'กนผ.', 'กบภ.', 'กปจว.', 'กปส.', 'กพน.', 'กสท.', 'งป.',
       'ผกง.', 'สกร.', 'สจว.']
        result = pd.DataFrame(raw_received_units, columns=classes)
        result['selected'] = result.apply(lambda row: row.index[row == 1].tolist(), axis=1)

        response_dict = {"received_units": np.array(result['selected']).flatten()[0]}
        return Response(response_dict, status=200)
