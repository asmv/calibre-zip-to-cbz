from typing import List
import enum
import pathlib
import tempfile
import xml.etree.ElementTree as et
import xml.dom.minidom as md


class ComicInfoSchemaVersion(enum.Enum):
    V1_0 = pathlib.Path('../comicinfo/schema/v1.0/ComicInfo.xsd')
    V2_0 = pathlib.Path('../comicinfo/schema/v2.0/ComicInfo.xsd')
    V2_1 = pathlib.Path('../comicinfo/drafts/v2.1/ComicInfo.xsd')


class ComicInfo:

    def __init__(self, schema_version: ComicInfoSchemaVersion):
        self._schema_version = schema_version
        ## Schema
        ### V1.0
        self.title : str = None
        self.series : str = None
        self.number : str = None
        self.count : int = None
        self.volume : int = None
        self.alternate_series : str = None
        self.alternate_number : str = None
        self.alternate_count : int = None
        self.summary : str = None
        self.notes : str = None
        self.year : int = None
        self.month : int = None
        self.writer : str = None
        self.penciller : str = None
        self.inker : str = None
        self.colorist : str = None
        self.letterer : str = None
        self.cover_artist : str = None
        self.editor: str = None
        self.publisher : str = None
        self.imprint : str = None
        self.genre : str = None
        self.web : str = None
        self.page_count : int = None
        self.language_ISO : str = None
        self.format : str = None
        self.black_and_white : str = None
        self.manga : str = None
        # pages not supported
        ### V2.0
        self.characters : str = None
        self.teams : str = None
        self.locations : str = None
        self.scan_information : str = None
        self.story_arc : str = None
        self.series_group : str = None
        self.age_rating : str = None
        self.day : int = None
        self.community_rating : float = None
        self.main_character_or_team : str = None
        self.review : str = None
        ### V2.1
        self.tags : str = None
        self.translator : str = None
        self.story_arc_number : int = None

    def to_comic_info_xml(self) -> str:
        comic_info_schema_attributes: List[str]
        with open(pathlib.Path(__file__).parent.joinpath(self._schema_version.value), "r") as schema_file:
            schema = et.parse(schema_file)
            comic_info_complex_type_schema = schema.findall('./xs:complexType[@name="ComicInfo"]', {'xs': 'http://www.w3.org/2001/XMLSchema'})[0]
            comic_info_schema_attributes = [element.attrib['name'] for element in comic_info_complex_type_schema[0] if 'name' in element.attrib]
        comic_info = et.Element('ComicInfo')
        for attrib, value in vars(self).items():
            if not attrib.startswith("_"):
                xml_attrib_name = ''.join([s[0].upper() + s[1:] for s in attrib.split('_') if len(s) > 0])
                if xml_attrib_name in comic_info_schema_attributes and value is not None:
                    element = et.Element(xml_attrib_name)
                    element.text = str(value)
                    comic_info.insert(0, element)
        with tempfile.SpooledTemporaryFile(max_size=8000000, mode="wb+") as temp_file:
            et.ElementTree.write(et.ElementTree(comic_info), temp_file, xml_declaration=True, encoding='UTF-8', method='xml', short_empty_elements=False)
            temp_file.seek(0)
            return md.parseString(temp_file.read().decode()).toprettyxml().strip()
