import pickle as pkl
import time
import networkx as nx
import csv
from lxml import etree
from linkage.DSB import *

slownet_xml_filepath = '../../res/slownet-2015-05-07.xml'
slownet_translated_graph_filepath = '../../res/slownet_extended.graph'
dsb_slownet_links_filepath = '../../res/dsb_slownet_links.csv'
slownet_extended_output_filepath = '../../res/slownet_extended.xml'
slownet_dsb_extended_filepath = '../../res/slownet_dsb_extended.graph'
final_extended_slownet_filepath = '../../res/slownet_dsb_extended.xml'

class SloWNet_Extender:

    def __init__(self):
        self.dsb = DSB()
        links_csv = open(dsb_slownet_links_filepath)
        self.dsb_links = csv.DictReader(links_csv, delimiter='|')
        self.slownet = pkl.load(open(slownet_translated_graph_filepath, 'rb'))
        self.syntactic_structure_map = self.get_syntactic_structure_form_map()

    def is_strong(self, link):
        return (
            link['dsb_dummy_sense'] == 'False' and
            int(link['number_of_synset_literals']) > 1 and
            (int(link['matched_synonyms']) > 0 or
             int(link['matched_antonyms']) > 0 or
             int(link['matched_hypernyms']) > 0)
        )

    def get_strong_links(self):
        synset_links = dict()
        for link in self.dsb_links:
            if (self.is_strong(link)):
                synset_id = link['slownet_synset_id']
                dsb_sense_id = int(link['dsb_sense_id'])
                if (not synset_id in synset_links):
                    synset_links[synset_id] = []
                synset_links[synset_id].append(dsb_sense_id)
        
        return synset_links 
    
    def get_syntactic_structure_form_map(self):
        query = self.dsb.session.query(Extension).filter(Extension.name == 'structures').first()
        parser = etree.XMLParser(remove_blank_text=True)
        data = etree.fromstring(query.string, parser=parser)
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
        parts = self.dsb.session.query(LexicalUnitPart.id, FormEncoding.text)\
                                .join(LexicalUnit, LexicalUnitPart.lexical_unit_id == LexicalUnit.id)\
                                .join(StructureComponent, LexicalUnitPart.structure_component_id == StructureComponent.id)\
                                .join(FormEncoding, LexicalUnitPart.form_encoding_id == FormEncoding.id)\
                                .filter(LexicalUnit.id == lexical_unit_id)\
                                .order_by(StructureComponent.index)\
                                .all()
        return parts
    
    def get_form(self, lexical_unit):
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
        return full_form
    
    def get_synonyms(self, sense_id):
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
                                    SenseRelationType.name == 'synonym')\
                                  .all()
        synonyms = []
        for match in matches:
            synonym_lexical_unit = self.dsb.session.query(LexicalUnit).get(match.related_lexical_unit_id)
            form = self.get_form(synonym_lexical_unit)
            synonyms.append(form)

        return synonyms
    
    def get_definitions(self, sense_id):
        matches = self.dsb.session.query(Definition)\
                                .filter(Definition.sense_id == sense_id)\
                                .all()
        return matches

    def extend_slownet_graph(self):
        strong_links = self.get_strong_links()
        synset_ctr = 0
        for synset_id in strong_links.keys():

            slo_literals = self.slownet.nodes[synset_id]['slo_literals']
            slo_definitions = []
            for dsb_sense_id in strong_links[synset_id]:

                dsb_synonyms = self.get_synonyms(dsb_sense_id)
                for synonym in dsb_synonyms:
                    slo_literals.append(synonym)

                dsb_definitions = self.get_definitions(dsb_sense_id)
                for definition in dsb_definitions:
                    if (len(definition.description.split()) > 1):
                        slo_definitions.append(definition.description)

            self.slownet.nodes[synset_id]['definitions'] = list(set(slo_definitions))
            self.slownet.nodes[synset_id]['slo_literals'] = list(set(slo_literals))

            synset_ctr += 1
            if (synset_ctr % 100 == 0):
                print(synset_ctr, '/', len(strong_links.keys()), 'synsets processed')

        with open(slownet_dsb_extended_filepath, 'wb') as slownet_dsb_extended_file:  
            pkl.dump(self.slownet, slownet_dsb_extended_file)

    def extend_slownet_xml(self):
        extended_slownet = pkl.load(open(slownet_dsb_extended_filepath, 'rb'))
        parser = etree.XMLParser(remove_blank_text=True)
        root_slownet = etree.parse(slownet_xml_filepath, parser=parser)
        synsets = root_slownet.xpath('//SYNSET')

        new_literal_ctr = 0
        new_definition_ctr = 0
        synset_ctr = 0
        for synset in synsets:
            synset_id = synset.xpath('ID/text()')[0]
            synonym_elements = synset.xpath('.//SYNONYM[@xml:lang="sl"]')
            if (len(synonym_elements) > 0):
                synonym_element = synonym_elements[0]
                old_literals = synonym_element.xpath('LITERAL/text()')
                all_literals = extended_slownet.nodes[synset_id]['slo_literals']
                new_literals = list(set(all_literals) - set(old_literals))

                for literal in new_literals:
                    new_literal = etree.SubElement(synonym_element, 'LITERAL', lnote='auto')
                    new_literal.text = literal
                    synonym_element.append(new_literal)
                    new_literal_ctr += 1

                if ('definitions' in extended_slownet.nodes[synset_id]):
                    definitions = extended_slownet.nodes[synset_id]['definitions']
                    for definition in definitions:
                        new_definition = etree.SubElement(synset, 'DEF')
                        new_definition.attrib[etree.QName('http://www.w3.org/XML/1998/namespace', 'lang')] = 'sl'
                        new_definition.attrib['lnote'] = 'auto'
                        new_definition.text = definition
                        synset.append(new_definition)
                        new_definition_ctr += 1

        root_slownet.write(final_extended_slownet_filepath, pretty_print=True, encoding='utf-8', xml_declaration=True)

        print(new_literal_ctr, 'new literals added')
        print(new_definition_ctr, 'new definitions added')


def main():
    t1 = time.time()
    extender = SloWNet_Extender()
    extender.extend_slownet_graph()
    extender.extend_slownet_xml()
    t2 = time.time() - t1
    print('TOTAL TIME ELAPSED: ' + str(t2))

if __name__ == '__main__':
    main()