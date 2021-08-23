# libnadagclient

Client library for the geotechnical database at https://geo.ngu.no/kart/nadag/

This library parses the web pages for soundings, as well as zip-files of SGF (.TOT, .CPT) files uploaded by
users using [libsgfdata](https://github.com/emerald-geomodelling/libsgfdata).

The data is combined and exposed using the [libsgfdata](https://github.com/emerald-geomodelling/libsgfdata) datamodel.

# Usage

    >>> import libnadagclient 

Look up project NADAG IDs (and their project numbers, as specified by
the uploading user, if any) using a bounding box:

    >>> libnadagclient.get_project_ids_from_bounds((313156.8520104526, 6671055.691595874, 339199.23407153715, 6686819.705570765))
    {'306dc437-08f8-40f2-a918-7f65c423611b': '20120920-L', 'bddca10a-ba33-4aa8-82bf-f89f4141b0e3': '101613', ...}

Look up a project NADAG ID using its project number:

    >>> libnadagclient.get_project_id("20120920-L")
    "306dc437-08f8-40f2-a918-7f65c423611b"

Download all boreholes of a project, merge in location information and other metadata from the webpages and store
them all in a single SGF file:

    >>> d = libnadagclient.get_project_borehole_data("306dc437-08f8-40f2-a918-7f65c423611b")
    >>> libsgfdata.dump(list(d.values()), "306dc437-08f8-40f2-a918-7f65c423611b.tot")
