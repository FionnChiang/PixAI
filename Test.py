import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from imgutils.tagging.pixai import get_pixai_tags

result = get_pixai_tags('figure/16E827A081C09E9C9C7C9D11E90FDD87.jpg',model_name='v0.9',thresholds={'general':0.3, 'character':0.5})
general_tags, character_tags = result
print("General tags:", general_tags)
print("Character tags:", character_tags)