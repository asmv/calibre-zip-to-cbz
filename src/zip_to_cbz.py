import argparse
import pathlib
import zipfile
import tempfile
import shutil
import comicinfo
import logging
logger = logging.getLogger(__file__)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("paths", nargs="+", help="The path to the Calibre library or multiple paths to a specific subfolders of that library. \
                                        The script will recursively operate on all zip files that also have a \
                                        metadata.opf file in the same folder.")
    parser.add_argument("--comicinfo-schema-version", "--schema", choices=["1.0", "2.0", "2.1"], default="2.0")
    parser.add_argument("--output-directory", "-o", type=pathlib.Path, help="Output resulting '.cbz' file to an alternate location.")
    parser.add_argument("--group-by-series", action="store_true", default=False, help="If an output directory is specified, group the resulting output by series name. 'Other' is used as the series name if the series is not present in metadata.")
    parser.add_argument("--tags-to-genre", action="store_true", default=False, help="Write Calibre subject (shown as 'Tags' in the GUI) to the 'genre' ComicInfo.xml field instead of the 'Tags' field in schema version 2.1+")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Enable Debug logging.")
    args = parser.parse_args()
    # Set Logging Level
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    schema_version: comicinfo.ComicInfoSchemaVersion = None
    # Set ComicInfo.xml schema version
    if args.comicinfo_schema_version == "1.0":
        logger.debug("Setting ComicInfo.xml schema version to v1.0")
        schema_version = comicinfo.ComicInfoSchemaVersion.V1_0
    elif args.comicinfo_schema_version == "2.0":
        logger.debug("Setting ComicInfo.xml schema version to v2.0")
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_0
    elif args.comicinfo_schema_version == "2.1":
        logger.debug("Setting ComicInfo.xml schema version to v2.1")
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_1
    for path in args.paths:
        logger.info('Processing files under path "%s"', path)
        for metadata_opf_file in pathlib.Path(path).rglob("metadata.opf"):
            zip_files = list(metadata_opf_file.parent.glob("*.zip"))
            if len(zip_files) == 0:
                continue
            logger.debug('Found metadata.opf file in directory "%s"', metadata_opf_file.parent)
            comic_info = comicinfo.ComicInfo.from_calibre_metadata_opf(metadata_opf_file, schema_version)
            for zip_file in zip_files:
                cbz_file = zip_file.with_suffix(".cbz")
                logger.info('Converting zip achive "%s" in directory "%s" to cbz file', zip_file.name, zip_file.parent)
                with tempfile.TemporaryDirectory() as temporary_directory:
                    temporary_directory_path = pathlib.Path(temporary_directory)
                    with zipfile.ZipFile(zip_file, "r") as source_zip:
                        logger.debug('Extracting zip achive "%s" to temporary directory "%s"', zip_file.name, temporary_directory_path)
                        source_zip.extractall(temporary_directory)
                    with zipfile.ZipFile(cbz_file, "w") as destination_cbz:
                        images_path = pathlib.Path("images")
                        cover = next(temporary_directory_path.glob("*/cover.*"), None)
                        if cover is not None:
                            cover_arcname = images_path.joinpath(f"000000_{cover.name}")
                            logger.debug('Writing cover image "%s" to cbz archive as "%s"', cover.relative_to(temporary_directory_path), cover_arcname)
                            destination_cbz.write(cover, cover_arcname)
                        else:
                            logger.warning("No cover file found for zip archive, skipping cover creation.")
                        page_count = 0
                        for image in temporary_directory_path.glob("*/OEBPS/image/*"):
                            image_arcname = images_path.joinpath(image.name)
                            logger.debug('Writing image "%s" to cbz archive as "%s"', image.relative_to(temporary_directory_path), image_arcname)
                            destination_cbz.write(image, image_arcname)
                            page_count += 1
                        if page_count == 0:
                            logger.error('NO PAGES found in zip archive "%s". The source format may not be supported. Try unzipping the archive and checking the format of the contained images.', zip_file)
                        # Set PageCount manually here since metadata.opf does not contain that information
                        logger.debug("Setting PageCount of comicinfo to %i", page_count)
                        comic_info.PageCount = page_count
                        with tempfile.NamedTemporaryFile(mode="w+", encoding="UTF-8", delete=False) as comicinfo_xml_temporary_file:
                            comicinfo_xml_temporary_file_path = pathlib.Path(comicinfo_xml_temporary_file.name)
                            logger.debug('Serializing ComicInfo.xml of temporary file "%s"', comicinfo_xml_temporary_file_path)
                            comic_info.to_comic_info_xml(comicinfo_xml_temporary_file_path)
                            logger.debug("Writing ComicInfo.xml")
                            destination_cbz.write(comicinfo_xml_temporary_file_path, "ComicInfo.xml")
                    if args.output_directory is not None:
                        destination: pathlib.Path
                        if args.group_by_series:
                            destination = args.output_directory.joinpath(comic_info.Series, cbz_file.name) if comic_info.Series is not None else args.output_directory.joinpath("Other", cbz_file.name)
                        else:
                            destination = args.output_directory.joinpath(cbz_file.name) if args.group_by_series else args.output_directory.joinpath(cbz_file.name)
                        if not destination.parent.exists():
                            logger.info('Creating output directory "%s"', destination.parent)
                            destination.parent.mkdir(parents=True)
                        if destination.exists() and destination.is_file():
                            logger.warning('Deleted existing cbz file "%s"', destination)
                            destination.unlink()
                        logger.info('Moving generated cbz file "%s" to "%s"', cbz_file, destination)
                        shutil.move(cbz_file, destination)


if __name__ == "__main__":
    main()
