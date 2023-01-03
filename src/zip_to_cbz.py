import argparse
import pathlib
import zipfile
import tempfile
import shutil
import comicinfo

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("paths", nargs="+", help="The path to the Calibre library or multiple paths to a specific subfolders of that library. \
                                        The script will recursively operate on all zip files that also have a \
                                        metadata.opf file in the same folder.")
    parser.add_argument("--comicinfo-schema-version", "--schema", choices=["1.0", "2.0", "2.1"], default="2.0")
    parser.add_argument("--output-directory", "-o", type=pathlib.Path, help="Output resulting '.cbz' file to an alternate location.")
    parser.add_argument("--group-by-series", action="store_true", default=False, help="If an output directory is specified, group the resulting output by series name. 'Other' is used as the series name if the series is not present in metadata.")
    args = parser.parse_args()
    schema_version: comicinfo.ComicInfoSchemaVersion = None
    if args.comicinfo_schema_version == "1.0":
        schema_version = comicinfo.ComicInfoSchemaVersion.V1_0
    elif args.comicinfo_schema_version == "2.0":
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_0
    elif args.comicinfo_schema_version == "2.1":
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_1
    for path in args.paths:
        for metadata_opf_file in pathlib.Path(path).rglob("metadata.opf"):
            comic_info = comicinfo.ComicInfo.from_calibre_metadata_opf(metadata_opf_file, schema_version)
            for zip_file in metadata_opf_file.parent.glob("*.zip"):
                cbz_file = zip_file.with_suffix(".cbz")
                with tempfile.TemporaryDirectory() as temporary_directory:
                    temporary_directory_path = pathlib.Path(temporary_directory)
                    with zipfile.ZipFile(zip_file, "r") as source_zip:
                        source_zip.extractall(temporary_directory)
                    with zipfile.ZipFile(cbz_file, "w") as destination_cbz:
                        images_path = pathlib.Path("images")
                        cover = next(temporary_directory_path.glob("*/cover.*"), None)
                        if cover is not None:
                            destination_cbz.write(cover, images_path.joinpath(f"000000_{cover.name}"))
                        page_count = 0
                        for image in temporary_directory_path.glob("*/OEBPS/image/*"):
                            destination_cbz.write(image, images_path.joinpath(image.name))
                            page_count += 1
                        # Set PageCount manually here since metadata.opf does not contain that information
                        comic_info.PageCount = page_count
                        with tempfile.NamedTemporaryFile(mode="w+", encoding="UTF-8", delete=False) as comicinfo_xml_temporary_file:
                            comicinfo_xml_temporary_file_path = pathlib.Path(comicinfo_xml_temporary_file.name)
                            comic_info.to_comic_info_xml(comicinfo_xml_temporary_file_path)
                            destination_cbz.write(comicinfo_xml_temporary_file_path, "ComicInfo.xml")
                    if args.output_directory is not None:
                        destination: pathlib.Path
                        if args.group_by_series:
                            destination = args.output_directory.joinpath(comic_info.Series, cbz_file.name) if comic_info.Series is not None else args.output_directory.joinpath("Other", cbz_file.name)
                        else:
                            destination = args.output_directory.joinpath(cbz_file.name) if args.group_by_series else args.output_directory.joinpath(cbz_file.name)
                        destination.parent.mkdir(exist_ok=True, parents=True)
                        if destination.exists() and destination.is_file():
                            destination.unlink()
                        shutil.move(cbz_file, destination)


if __name__ == "__main__":
    main()
