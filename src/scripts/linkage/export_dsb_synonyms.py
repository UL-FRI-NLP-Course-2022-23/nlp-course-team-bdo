from DSB import *
import lxml.etree as lxml
import csv, time
from datetime import datetime  

class DSB_exporter:

    def __init__(self):
        self.dsb = DSB()
        self.syntactic_structure_map = self.get_syntactic_structure_form_map()
        self.lexical_unit_forms = dict()

    def get_lexical_units_with_status(self):
        # Get headwords from the 'ssss' resource

        matches = self.dsb.session.query(
                                    LexicalUnit.id,
                                    LexicalUnit.syntactic_structure_id,
                                    LexicalUnitType.name.label('type'))\
                                  .join(LexicalUnitType, LexicalUnit.type_id == LexicalUnitType.id)\
                                  .join(LexicalUnitStatus, LexicalUnit.id == LexicalUnitStatus.lexical_unit_id)\
                                  .join(ResourceStatus, LexicalUnitStatus.resource_status_id == ResourceStatus.id)\
                                  .join(Resource, ResourceStatus.resource_id == Resource.id)\
                                  .filter(
                                    Resource.name == 'ssss')\
                                  .all()
        return matches
                                      

    def get_lexical_unit_senses(self, lexical_unit_id):
        # Get senses of the given lexical unit

        matches = self.dsb.session.query(Sense)\
                                  .filter(Sense.lexical_unit_id == lexical_unit_id)\
                                  .all()
        return matches

    def get_sense_relations(self, sense_id):
        # Get relevant sense relations from the given sense

        matches = self.dsb.session.query(
                                    SenseRelation.id,
                                    SenseRelation.from_sense_id,
                                    SenseRelation.to_sense_id,
                                    SenseRelationType.name.label('type'),
                                    Sense.lexical_unit_id.label('related_lexical_unit_id'))\
                                  .join(SenseRelationType, SenseRelation.type_id == SenseRelationType.id)\
                                  .join(Sense, SenseRelation.to_sense_id == Sense.id)\
                                  .filter(
                                    SenseRelation.from_sense_id == sense_id,
                                    SenseRelationType.name.in_(['synonym', 'antonym', 'hypernym', 'hyponym']))\
                                  .all()
        return matches

    def get_lexical_unit_category(self, lexical_unit_id):
        # Get the category of given lexical unit

        match = self.dsb.session.query(Category)\
                                .join(Lexeme, Category.id == Lexeme.category_id)\
                                .join(WordForm, Lexeme.id == WordForm.lexeme_id)\
                                .join(FormRepresentation, WordForm.id == FormRepresentation.word_form_id)\
                                .join(FormEncoding, FormRepresentation.id == FormEncoding.form_representation_id)\
                                .join(LexicalUnitPart, FormEncoding.id == LexicalUnitPart.form_encoding_id)\
                                .filter(LexicalUnitPart.lexical_unit_id == lexical_unit_id)\
                                .first()
        if match:
            return match.name
        return None

    def get_syntactic_structure_form_map(self):
        # Fill the map of syntactic structure contacts, to use when getting lexical unit forms

        query = self.dsb.session.query(Extension).filter(Extension.name == 'structures').first()
        parser = lxml.XMLParser(remove_blank_text=True)
        data = lxml.fromstring(query.string, parser=parser)
        structure_contacts = {}
        for xml in data:
            structure_id = xml.get('id')
            system = xml.xpath('system[@type="JOS"]')[0]
            core_count = len(system.xpath('components/component[@type="core"]'))
            components = system.xpath('definition/component')[:core_count]
            contacts = []
            for component in components:
                try:
                    contact = component.xpath('restriction[@type="space"]/feature[@contact]/@contact')[0]
                except IndexError:
                    contact = None
                contacts.append(contact)
            structure_contacts[structure_id] = contacts
        return structure_contacts
    
    def get_lexical_unit_parts(self, lexical_unit_id):
        # Get parts of a given lexical units

        parts = self.dsb.session.query(LexicalUnitPart.id, FormEncoding.text)\
                                .join(LexicalUnit, LexicalUnitPart.lexical_unit_id == LexicalUnit.id)\
                                .join(StructureComponent, LexicalUnitPart.structure_component_id == StructureComponent.id)\
                                .join(FormEncoding, LexicalUnitPart.form_encoding_id == FormEncoding.id)\
                                .filter(LexicalUnit.id == lexical_unit_id)\
                                .order_by(StructureComponent.index)\
                                .all()
        return parts

    def get_form(self, lexical_unit):
        # Get the for of a given lexical unit

        full_form = ''
        contacts = self.syntactic_structure_map[str(lexical_unit.syntactic_structure_id)]
        parts = self.get_lexical_unit_parts(lexical_unit.id)
        for (lup, contact) in zip(parts, contacts):
            if (contact in {'both', 'left'}):
                full_form = full_form[:-1]
            full_form += lup.text
            if (contact not in {'both', 'right'}):
                full_form += ' '

        full_form = full_form.strip()
        self.lexical_unit_forms[lexical_unit.id] = full_form
        return full_form
    
    def get_related_forms(self, sense_id):
        synonyms = list()
        antonyms = list()
        hypernyms = list()
        hyponyms = list()
        sense_relations = self.get_sense_relations(sense_id)

        for relation in sense_relations:
            if (relation.related_lexical_unit_id in self.lexical_unit_forms):
                related_sense_form = self.lexical_unit_forms[relation.related_lexical_unit_id]
            else:
                related_lexical_unit = self.dsb.session.query(LexicalUnit).get(relation.related_lexical_unit_id)
                related_sense_form = self.get_form(related_lexical_unit)

            if (relation.type == 'synonym'):
                synonyms.append(related_sense_form)
            elif (relation.type == 'antonym'):
                antonyms.append(related_sense_form)
            elif (relation.type == 'hypernym'):
                hypernyms.append(related_sense_form)
            elif (relation.type == 'hyponym'):
                hyponyms.append(related_sense_form)

        related_forms = {
            'synonyms': synonyms,
            'antonyms': antonyms,
            'hypernyms': hypernyms,
            'hyponyms': hyponyms,
        }
        return related_forms
        
    def export_data(self):
        csv_file = open('../../../res/dsb_data.csv', 'w')
        fieldnames = [
            'lexical_unit_id',
            'lexical_unit_type',
            'lexical_unit_category',
            'form',
            'sense_id',
            'sense_position',
            'synonyms',
            'antonyms',
            'hypernyms',
            'hyponyms'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter='|')
        writer.writeheader()

        lexical_units = self.get_lexical_units_with_status()

        for unit in lexical_units:
            category = None
            if (unit.type == 'single_lexeme_unit'):
                category = self.get_lexical_unit_category(unit.id)
            if (unit.id in self.lexical_unit_forms):
                form = self.lexical_unit_forms[unit.id]
            else:
                form = self.get_form(unit)
            
            senses = self.get_lexical_unit_senses(unit.id)

            for sense in senses:
                related_forms = self.get_related_forms(sense.id)
                csv_row = {
                    'lexical_unit_id': unit.id,
                    'lexical_unit_type': unit.type,
                    'lexical_unit_category': category,
                    'form': form,
                    'sense_id': sense.id,
                    'sense_position': sense.position,
                    'synonyms': ';'.join(related_forms['synonyms']),
                    'antonyms': ';'.join(related_forms['antonyms']),
                    'hypernyms': ';'.join(related_forms['hypernyms']),
                    'hyponyms': ';'.join(related_forms['hyponyms'])
                }
                writer.writerow(csv_row)
        csv_file.close()

def main():
    t1 = time.time()
    exporter = DSB_exporter()
    exporter.export_data()
    t2 = time.time() - t1
    print('TOTAL TIME ELAPSED: ' + str(t2))

if __name__ == "__main__":
    main()
