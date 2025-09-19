import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from imgutils.tagging.pixai import get_pixai_tags

result = get_pixai_tags('figure/3E3DC9811DCFB268704D7638A63997BD.jpg',model_name='v0.9',thresholds={'general':0.3, 'character':0.5})
general_tags, character_tags = result
print("General tags:", general_tags)
print("Character tags:", character_tags)