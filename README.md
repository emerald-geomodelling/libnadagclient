# libnadagclient

Client library for the geotechnical database at https://geo.ngu.no/kart/nadag/

This library parses the web pages for soundings, as well as zip-files of SGF (.TOT, .CPT) files uploaded by
users using [libsgfdata](https://github.com/emerald-geomodelling/libsgfdata).

The data is combined and exposed using the [libsgfdata](https://github.com/emerald-geomodelling/libsgfdata) datamodel.

# Usage

Look up a project NADAG ID using its project number (as specified by the uploading user):

    >>> import libnadagclient 
    >>> libnadagclient.get_project_id("10207634-02")
    "b9b39468-4923-454b-a058-9ac6eaf8f902"

Download all boreholes of a project, merge in location information and other metadata from the webpages and store
them all in a single SGF file:

    >>> d = libnadagclient.get_project_borehole_data("b9b39468-4923-454b-a058-9ac6eaf8f902")
    >>> libsgfdata.dump(list(d.values()), "b9b39468-4923-454b-a058-9ac6eaf8f902.tot")
