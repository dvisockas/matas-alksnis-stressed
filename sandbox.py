from vdu_nlp_services import stress_text
from zipfile import ZipFile
from conllu import parse_incr
from io import TextIOWrapper
from grammar_map import matas_service_pairs, matas_service_opposite_pairs, service_matas_tag_map
import re

matas_archive_filename = './dataset/MATAS-v1.0.zip'

stress_pattern = re.compile(r'(\d+\.)\s+([^\(]+)\s+\(([^\)]+)\)')
matas_conllu_filename_pattern = re.compile(r'MATAS-v1\.0\/CONLLU\/.*\.conllu')
tag_pattern = re.compile(r'[\w-]+\.')

def stress(word):
	res = stress_text(word.strip()).splitlines()

	for line in res:
		m = stress_pattern.match(line)
		if m:
			word = m.group(2)
			details = m.group(3).split(' ')
			yield {'word': word, 'details': details}
		else:
			yield {'word': word, 'details': []}

def get_dataset_connlu_files(encoding='utf-8'):
	with ZipFile(matas_archive_filename, 'r') as zip_ref:
		for filename in zip_ref.namelist():
			if matas_conllu_filename_pattern.match(filename):
				with zip_ref.open(filename, 'r') as fp:
					with TextIOWrapper(fp, encoding=encoding) as text_fp:
						yield text_fp


def convert_stress_to_matas_tags(stress_tags, matas_tags=None):
	if matas_tags:
		for matas_tag, stress_tag in matas_service_opposite_pairs:
			if stress_tag in stress_tags and matas_tag in matas_tags:
				raise Exception()
	
	for tag in stress_tags:
		if service_matas_tag_map[tag]:
			yield service_matas_tag_map[tag]

def get_stessed_sentences():
	for fp in get_dataset_connlu_files():
		for tokenlist in parse_incr(fp):
			offset = 0
			sentence = tokenlist.metadata['text']
			sentence_parts = []
			
			for token in tokenlist:
				word = token['form']

				word_offset = sentence.find(word, offset)
				
				glue = sentence[offset: word_offset]
			
				if glue:
					sentence_parts.append( (glue, glue) )

				stress_options = []

				for each in stress(word):
					stress_tag_set = set(each['details'])

					matas_tag_set = set([])
					for tag in tag_pattern.finditer(token['xpos']):
						matas_tag_set.add(tag.group(0))
					
					converted_stress_tags = list(convert_stress_to_matas_tags(stress_tag_set, matas_tag_set))
					tags = set(converted_stress_tags).difference( matas_tag_set )
					stress_options.append( (len(tags), each['word']) )

				stress_options.sort(key=lambda a: a[0])

				sentence_parts.append( (word, stress_options[0][1]) )

				offset = word_offset + len(word)

			glue = sentence[offset:]

			if glue:
				sentence_parts.append( (glue, glue) )

			yield sentence_parts

for sentence in get_stessed_sentences():
	print(sentence)
	print()
