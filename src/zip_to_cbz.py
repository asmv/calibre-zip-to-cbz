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
    for metadata_opf_file in pathlib.Path(args.path).rglob("metadata.opf"):
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


if __name__ == "__main__":
    main()
