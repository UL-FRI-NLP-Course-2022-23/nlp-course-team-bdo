from sqlalchemy import create_engine  
from sqlalchemy.ext.declarative import declarative_base  
from sqlalchemy.orm import Session
import os


if 'DSB_STRING' in os.environ:
    dsb_conn_str = os.environ['DSB_STRING']
else:
    dsb_conn_str = "postgresql://dsb_user@localhost:5432/superbaza"

Base = declarative_base()
engine = create_engine(dsb_conn_str)
Base.metadata.reflect(engine)

class DSB:
    def __init__(self):
        self.engine = create_engine(dsb_conn_str)
        self.session = Session(self.engine)

class LexicalUnit(Base):
    __table__ = Base.metadata.tables['jedro_lexicalunit']

class LexicalUnitType(Base):
    __table__ = Base.metadata.tables['jedro_lexicalunittype']

class LexicalUnitStatus(Base):
    __table__ = Base.metadata.tables['jedro_lexicalunit_status']

class LexicalUnitPart(Base):
    __table__ = Base.metadata.tables['jedro_lexicalunitpart']

class Lexeme(Base):
    __table__ = Base.metadata.tables['jedro_lexeme']

class ResourceStatus(Base):
    __table__ = Base.metadata.tables['jedro_resource_status']

class Sense(Base):
    __table__ = Base.metadata.tables['jedro_sense']

class SenseRelation(Base):
    __table__ = Base.metadata.tables['jedro_senserelation']

class SenseRelationType(Base):
    __table__ = Base.metadata.tables['jedro_senserelationtype']

class Example(Base):
    __table__ = Base.metadata.tables['jedro_example']

class SenseExample(Base):
    __table__ = Base.metadata.tables['jedro_sense_example']

class ExampleSentence(Base):
    __table__ = Base.metadata.tables['jedro_examplesentence']

class SenseExampleToken(Base):
    __table__ = Base.metadata.tables['jedro_senseexampletoken']   

class Status(Base):
    __table__ = Base.metadata.tables['jedro_status']

class Category(Base):
    __table__ = Base.metadata.tables['jedro_category']

class Definition(Base):
    __table__ = Base.metadata.tables['jedro_definition']

class DefinitionType(Base):
    __table__ = Base.metadata.tables['jedro_definitiontype']

class FeatureValue(Base):
    __table__ = Base.metadata.tables['jedro_featurevalue']

class FeatureValueRelation(Base):
    __table__ = Base.metadata.tables['jedro_featurevaluerelation']

class Feature(Base):
    __table__ = Base.metadata.tables['jedro_feature']

class Resource(Base):
    __table__ = Base.metadata.tables['jedro_resource']

class Corpus(Base):
    __table__ = Base.metadata.tables['jedro_corpus']

class FeatureCategory(Base):
    __table__ = Base.metadata.tables['jedro_featurecategory']

class FormEncoding(Base):
    __table__ = Base.metadata.tables['jedro_formencoding']

class FormRepresentation(Base):
    __table__ = Base.metadata.tables['jedro_formrepresentation']

class FormRepresentationType(Base):
    __table__ = Base.metadata.tables['jedro_formrepresentationtype']

class LemmaFormRepresentation(Base):
    __table__ = Base.metadata.tables['jedro_lemma_formrepresentation']

class WordForm(Base):
    __table__ = Base.metadata.tables['jedro_wordform']

class ExternalSource(Base):
    __table__ = Base.metadata.tables['jedro_externalsource']

class ObjectFeature(Base):
    __table__ = Base.metadata.tables['jedro_object_feature']

class ContentType(Base):
    __table__ = Base.metadata.tables['django_content_type']

class SensePart(Base):
    __table__ = Base.metadata.tables['jedro_sensepart']

class Measure(Base):
    __table__ = Base.metadata.tables['jedro_measure']

class SenseMeasure(Base):
    __table__ = Base.metadata.tables['jedro_sense_measure']

class Extension(Base):
    __table__ = Base.metadata.tables['jedro_extension']

class StructureComponent(Base):
    __table__ = Base.metadata.tables['jedro_structurecomponent']

    