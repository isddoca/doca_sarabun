import os
import pickle

from django.apps import AppConfig
from gensim.models import Doc2Vec
from gensim.test.test_doc2vec import ConcatenatedDoc2Vec

from config import settings


class DocClassifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doc_classify'
    D2V_FILE_1 = os.path.join(settings.MODELS, "v300e250w5-dbow.vec")
    D2V_FILE_2 = os.path.join(settings.MODELS, "v300e250w5-dm.vec")
    MODEL_FILE = os.path.join(settings.MODELS, "v300_e250_w5-dbow_dm.pkl")
    DICT_FILE = os.path.join(settings.RESOURCES, "dict.txt")
    d2v_dbow = Doc2Vec.load(D2V_FILE_1)
    d2v_dm = Doc2Vec.load(D2V_FILE_2)
    d2v = ConcatenatedDoc2Vec([d2v_dbow, d2v_dm])
    model = pickle.load(open(MODEL_FILE, 'rb'))
