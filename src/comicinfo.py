from typing import Set
import enum
import pathlib
import xml.etree.ElementTree as et
import html.parser
import functools
import json


XML_NAMESPACES = {
    'xs': 'http://www.w3.org/2001/XMLSchema',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf'
}


class _HTMLDataParser(html.parser.HTMLParser):

    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        self.string_representation = ""
        super().__init__(convert_charrefs=convert_charrefs)

    def handle_data(self, data: str) -> None:
        self.string_representation += data


class ComicInfoSchemaVersion(enum.Enum):
    V1_0 = pathlib.Path('../comicinfo/schema/v1.0/ComicInfo.xsd')
    V2_0 = pathlib.Path('../comicinfo/schema/v2.0/ComicInfo.xsd')
    V2_1 = pathlib.Path('../comicinfo/drafts/v2.1/ComicInfo.xsd')


class ComicInfo:

    def __init__(self, schema_version: ComicInfoSchemaVersion):
        self._schema_version = schema_version
        ## Schema
        ### V1.0
        self.Title : str = None
        self.Series : str = None
        self.Number : str = None
        self.Count : int = None
        self.Volume : int = None
        self.AlternateSeries : str = None
        self.AlternateNumber : str = None
        self.AlternateCount : int = None
        self.Summary : str = None
        self.Notes : str = None
        self.Year : int = None
        self.Month : int = None
        self.Writer : str = None
        self.Penciller : str = None
        self.Inker : str = None
        self.Colorist : str = None
        self.Letterer : str = None
        self.CoverArtist : str = None
        self.Editor: str = None
        self.Publisher : str = None
        self.Imprint : str = None
        self.Genre : str = None
        self.Web : str = None
        self.PageCount : int = None
        self.LanguageISO : str = None
        self.Format : str = None
        self.BlackAndWhite : str = None
        self.Manga : str = None
        # pages not supported
        ### V2.0
        self.Characters : str = None
        self.Teams : str = None
        self.Locations : str = None
        self.ScanInformation : str = None
        self.StoryArc : str = None
        self.SeriesGroup : str = None
        self.AgeRating : str = None
        self.Day : int = None
        self.CommunityRating : float = None
        self.MainCharacterOrTeam : str = None
        self.Review : str = None
        ### V2.1
        self.Tags : str = None
        self.Translator : str = None
        self.StoryArcNumber : int = None

    @staticmethod
    @functools.lru_cache(maxsize=3)
    def _comicinfo_schema_attribute_names(schema_version: ComicInfoSchemaVersion) -> Set[str]:
        with open(pathlib.Path(__file__).parent.joinpath(schema_version.value), "r") as schema_file:
            schema = et.parse(schema_file)
            comic_info_complex_type_schema = schema.findall('./xs:complexType[@name="ComicInfo"]', XML_NAMESPACES)[0]
            return {element.attrib['name'] for element in comic_info_complex_type_schema[0] if 'name' in element.attrib}

    @staticmethod
    def from_calibre_metadata_opf(calibre_metadata_opf_path: pathlib.Path, schema_version: ComicInfoSchemaVersion):
        comic_info = ComicInfo(schema_version)
        metadata_opf: et.Element = et.parse(calibre_metadata_opf_path).getroot()
        # Set ComicInfo attributes
        title_element = metadata_opf.find(".//dc:title", XML_NAMESPACES)
        if title_element is not None:
            comic_info.Title = title_element.text
        description_element = metadata_opf.find(".//dc:description", XML_NAMESPACES)
        if description_element is not None:
            html_parser = _HTMLDataParser()
            html_parser.feed(description_element.text)
            comic_info.Summary = html_parser.string_representation
        for attribute in ComicInfo._comicinfo_schema_attribute_names(schema_version):
            custom_column_element = metadata_opf.find(f'.//opf:meta[@name="calibre:user_metadata:#{attribute.lower()}"]', XML_NAMESPACES)
            if custom_column_element is not None:
                custom_column_content_json = json.loads(custom_column_element.attrib['content'])
                setattr(comic_info, attribute, custom_column_content_json['#value#'])
        return comic_info

    def to_comic_info_xml(self, xml_file: pathlib.Path):
        comic_info_schema_attributes = self._comicinfo_schema_attribute_names(self._schema_version)
        comic_info = et.Element('ComicInfo')
        for attrib, value in vars(self).items():
            if not attrib.startswith("_"):
                if attrib in comic_info_schema_attributes and value is not None:
                    element = et.Element(attrib)
                    element.text = str(value)
                    comic_info.insert(0, element)
        et.ElementTree.write(et.ElementTree(comic_info), xml_file, xml_declaration=True, encoding='UTF-8', method='xml', short_empty_elements=False)
