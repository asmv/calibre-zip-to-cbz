import argparse
import pathlib
import zipfile
import tempfile
import comicinfo

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("path", help="The path to the Calibre library or a specific subfolder of that library. \
                                        The script will recursively operate on all zip files that also have a \
                                        metadata.opf file in the same folder.")
    parser.add_argument("--comicinfo-schema-version", "--schema", choices=["1.0", "2.0", "2.1"], default="2.0")
    args = parser.parse_args()
    schema_version: comicinfo.ComicInfoSchemaVersion = None
    if args.comicinfo_schema_version == "1.0":
        schema_version = comicinfo.ComicInfoSchemaVersion.V1_0
    elif args.comicinfo_schema_version == "2.0":
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_0
    elif args.comicinfo_schema_version == "2.1":
        schema_version = comicinfo.ComicInfoSchemaVersion.V2_1
    for metadata_opf_file in pathlib.Path(args.path).rglob("metadata.opf"):
        comic_info = comicinfo.ComicInfo.from_calibre_metadata_opf(metadata_opf_file, schema_version)
        for zip_file in metadata_opf_file.parent.glob("*.zip"):
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_directory_path = pathlib.Path(temporary_directory)
                with zipfile.ZipFile(zip_file, "r") as source_zip:
                    source_zip.extractall(temporary_directory)
                with zipfile.ZipFile(zip_file.with_suffix(".cbz"), "w") as destination_cbz:
                    images_path = pathlib.Path("images")
                    cover = next(temporary_directory_path.glob("*/cover.*"), None)
                    if cover is not None:
                        destination_cbz.write(cover, images_path.joinpath(f"000000_{cover.name}"))
                    for image in temporary_directory_path.glob("*/OEBPS/image/*"):
                        destination_cbz.write(image, images_path.joinpath(image.name))
                    with tempfile.NamedTemporaryFile(mode="w+", encoding="UTF-8", delete=False) as comicinfo_xml_temporary_file:
                        comicinfo_xml_temporary_file_path = pathlib.Path(comicinfo_xml_temporary_file)
                        comic_info.to_comic_info_xml(comicinfo_xml_temporary_file_path)
                        destination_cbz.write(comicinfo_xml_temporary_file_path, "ComicInfo.xml")


if __name__ == "__main__":
    main()
