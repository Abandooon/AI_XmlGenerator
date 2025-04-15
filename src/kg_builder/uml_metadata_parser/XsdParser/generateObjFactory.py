import os

from src.data_processing.uml_metadata_parser.XsdParser.TypeMapping import mapXsdTypeToJava, to_pascal_case


def generate_object_factory(output_dir, package_name, mappings,objectFactoryTemplate):
    for map in mappings:
        map['element_type'] = mapXsdTypeToJava(map['element_name'], context='mixed') or to_pascal_case(map['element_name'])
        if map['complex_type'] == 'LParagraph' and map['element_name'] == 'FT':
            map['element_type'] = map['element_type'].replace("Overview", "")



