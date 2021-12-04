import json


def json_assembler(name_json_file, model_name):

    file = open(name_json_file, 'r', encoding='utf-8')

    dump = json.load(file)
    file.close()
    non_duplicate_dump = []
    for item in dump:
        if item not in non_duplicate_dump:
            non_duplicate_dump.append(item)

    new_dump = []
    for i in range(len(non_duplicate_dump)):
        django_structure = {
            'model': model_name,
            'pk': i + 1,
            'fields': non_duplicate_dump[i]
        }
        new_dump.append(django_structure)

    file = open('../../data/final.json', 'w', encoding='utf-8')
    file.write(json.dumps(new_dump, ensure_ascii=False))
    file.close()


json_assembler('ingredients.json', 'api.ingredient')
