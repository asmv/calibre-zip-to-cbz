from typing import Set
import enum
import pathlib
import xml.etree.ElementTree as et
import html.parser
import functools
import json
import datetime
import logging
logger = logging.getLogger(__file__)

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
        logger.debug('Reading ComicInfo XSD file "%s"', schema_version.value)
        with open(pathlib.Path(__file__).parent.joinpath(schema_version.value), "r") as schema_file:
            logger.debug('Parsing ComicInfo XSD file')
            schema = et.parse(schema_file)
            comic_info_complex_type_schema = schema.findall('./xs:complexType[@name="ComicInfo"]', XML_NAMESPACES)[0]
            return {element.attrib['name'] for element in comic_info_complex_type_schema[0] if 'name' in element.attrib}

    @staticmethod
    def from_calibre_metadata_opf(calibre_metadata_opf_path: pathlib.Path, schema_version: ComicInfoSchemaVersion, tags_to_genre: bool = False):
        logger.debug('Creating ComicInfo with Schema Version: "%s"', schema_version.name.lower().replace("_", "."))
        comic_info = ComicInfo(schema_version)
        logger.debug('Reading metadata.opf file "%s"', calibre_metadata_opf_path)
        metadata_opf: et.Element = et.parse(calibre_metadata_opf_path).getroot()
        # Set ComicInfo attributes
        ## Title
        title_element = metadata_opf.find(".//dc:title", XML_NAMESPACES)
        if title_element is not None:
            comic_info.Title = title_element.text
            logger.debug('Set Title to: "%s"', comic_info.Title)
        ## Series
        series_element = metadata_opf.find(".//opf:meta[@name='calibre:series']", XML_NAMESPACES)
        if series_element is not None:
            comic_info.Series = series_element.attrib['content']
            logger.debug('Set Series to: "%s"', comic_info.Series)
        ## Series Number
        series_element = metadata_opf.find(".//opf:meta[@name='calibre:series_index']", XML_NAMESPACES)
        if series_element is not None:
            comic_info.Number = series_element.attrib['content']
            logger.debug('Set Number to: "%s"', comic_info.Number)
        ## Publisher
        publisher_element = metadata_opf.find(".//dc:publisher", XML_NAMESPACES)
        if publisher_element is not None:
            comic_info.Publisher = publisher_element.text
            logger.debug('Set Publisher to: "%s"', comic_info.Publisher)
        ## Date
        date_element = metadata_opf.find(".//dc:date", XML_NAMESPACES)
        if date_element is not None:
            date = datetime.datetime.fromisoformat(date_element.text)
            comic_info.Year = date.year
            comic_info.Month = date.month
            comic_info.Day = date.day
            logger.debug('Set Year to: "%i"', comic_info.Year)
            logger.debug('Set Month to: "%i"', comic_info.Month)
            logger.debug('Set Day to: "%i"', comic_info.Day)
        ## Language
        language_element = metadata_opf.find(".//dc:language", XML_NAMESPACES)
        if language_element is not None:
            comic_info.LanguageISO = language_element.text
            logger.debug('Set LanguageISO to: "%s"', comic_info.LanguageISO)
        ## Description
        description_element = metadata_opf.find(".//dc:description", XML_NAMESPACES)
        if description_element is not None:
            html_parser = _HTMLDataParser()
            html_parser.feed(description_element.text)
            comic_info.Summary = html_parser.string_representation
            logger.debug('Set Summary to: "%s"', comic_info.Summary)
        ## Tags/ Genre
        tag_elements = metadata_opf.findall(".//dc:subject", XML_NAMESPACES)
        if len(tag_elements) > 0:
            tags_comma_separated = ','.join([element.text for element in tag_elements])
            if tags_to_genre:
                comic_info.Genre = tags_comma_separated
                logger.debug('Set Genre to: "%s"', comic_info.Genre)
            else:
                comic_info.Tags = tags_comma_separated
                logger.debug('Set Tags to: "%s"', comic_info.Tags)
        ## Calibre Custom Columns (must be same case as ComicInfo tag or lowercase)
        for attribute in ComicInfo._comicinfo_schema_attribute_names(schema_version):
            custom_column_element = metadata_opf.find(f'.//opf:meta[@name="calibre:user_metadata:#{attribute}"]', XML_NAMESPACES)
            if custom_column_element is None:
                # Try lowercase attribute
                custom_column_element = metadata_opf.find(f'.//opf:meta[@name="calibre:user_metadata:#{attribute.lower()}"]', XML_NAMESPACES)
            if custom_column_element is not None:
                custom_column_content_json = json.loads(custom_column_element.attrib['content'])
                custom_column_element_value = custom_column_content_json['#value#']
                value = ','.join(custom_column_element_value) if type(custom_column_element_value) is list else custom_column_element_value
                setattr(comic_info, attribute, value)
                logger.debug('Set %s to: "%s"', attribute, value)
        return comic_info

    def to_comic_info_xml(self, xml_file: pathlib.Path):
        comic_info_schema_attributes = self._comicinfo_schema_attribute_names(self._schema_version)
        comic_info = et.Element('ComicInfo')
        for attrib, value in vars(self).items():
            if not attrib.startswith("_"):
                if attrib in comic_info_schema_attributes and value is not None:
                    element = et.Element(attrib)
                    element.text = str(value)
                    logger.debug('Adding attribute %s as child to ComicInfo', attrib)
                    comic_info.insert(0, element)
        logger.debug('Writing resulting ComicInfo XML to file "%s"', xml_file)
        et.ElementTree.write(et.ElementTree(comic_info), xml_file, xml_declaration=True, encoding='UTF-8', method='xml', short_empty_elements=False)
