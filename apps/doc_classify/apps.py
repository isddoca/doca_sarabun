import os
import pickle

from django.apps import AppConfig

from apps.app import settings


class DocClassifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doc_classify'
    D2V_FILE = os.path.join(settings.MODELS, "d2v-model_e250_v500_w5.pkl")
    MODEL_FILE = os.path.join(settings.MODELS, "logreg-model_e250_v500_w5.pkl")
    DICT_FILE = os.path.join(settings.RESOURCES, "dict.txt")
    print(MODEL_FILE)
    d2v = pickle.load(open(D2V_FILE, 'rb'))
    model = pickle.load(open(MODEL_FILE, 'rb'))
