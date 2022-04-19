import os
import pickle

from gensim.models import Doc2Vec

from config import settings
from django.apps import AppConfig


class DocClassifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doc_classify'
    D2V_FILE = os.path.join(settings.MODELS, "v400e200w5.vec")
    MODEL_FILE = os.path.join(settings.MODELS, "svm-model_e200_v400_w5.pkl")
    DICT_FILE = os.path.join(settings.RESOURCES, "dict.txt")
    d2v = Doc2Vec.load(D2V_FILE)
    model = pickle.load(open(MODEL_FILE, 'rb'))
