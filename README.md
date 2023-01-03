# calibre-zip-to-cbz

## About

This is a utility to convert the output of calibre's EPUB -> ZIP conversion to a CBZ (Comic Book Zip) file for use by comic book readers such as [Kavita](https://www.kavitareader.com/).

The conversion adds a ComicInfo.xml file into the resulting cbz file which provides metadata to supported applications.

**Note**: This program has no external code dependencies (on either pip packages or binaries) and should work on python versions 6.1 and above.

**Note**: This utility will only work for specific types of books, in particular those containing every page as an image file.

## Cloning the Repository

This repository contains a submodule for the ComicInfo.xml XSD definition files. To run the script you will need to clone the submodule using a command such as `git clone --recurse-submodules https://github.com/asmv/calibre-zip-to-cbz.git` (git 2.13+) or `git clone --recursive https://github.com/asmv/calibre-zip-to-cbz.git` (git 1.6.5+).

See [this stackoverflow answer](https://stackoverflow.com/questions/3796927/how-do-i-git-clone-a-repo-including-its-submodules) for more info.

## Usage

From the root directory of the repository:
`python3 src/zip_to_cbz.py /path/to/my/calibre/library/AuthorName/`

This will place a cbz file in the same folder as every zip file for all books under `AuthorName`.

### Other Arguments

`--comicinfo-schema-version`: Set the ComicInfo schema version. Either of `1.0`, `2.0`, or `2.1`. 

`--output-directory/-o`: Write the resulting cbz files to this folder instead of leaving them in the same location as the source zip files.

`--group-by-series`: If the output-directory option is set, group the resulting cbz files into folders by series.

`--tags-to-genre`: When creating the ComicInfo.xml file, write calibre tags to the Genre section instead of the Tags section. **Note**: The tags section is only available in ComicInfo.xml schema version 2.1

`--verbose`: Print out additional debug info.

As an example, for creating files for Kavita, you can use this command string:

`python3 src/zip_to_cbz.py -o output_cbz_files --group-by-series --comicinfo-schema-version 2.1 /path/to/my/calibre/library/AuthorName/`

## Adding Additional Fields to ComicInfo.xml

To add additional fields, such as `AgeRating`, you can create a custom column in calibre using "Preferences"/ "Settings" -> "Add Your Own Columns". Use either the same case or lowercase version of the ComicInfo.xml field.

See [The Anansi Project ComicInfo Documentation page](https://anansi-project.github.io/docs/comicinfo/documentation) for names and descriptions of the available ComicInfo fields.
