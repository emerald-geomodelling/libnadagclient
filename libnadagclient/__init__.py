import requests_html
import urllib.parse
import zipfile
import io
import libsgfdata
import requests
import lxml.etree
from owslib.wfs import WebFeatureService
from owslib import crs
import logging

logger = logging.getLogger(__name__)

session = requests_html.HTMLSession()

URL_PROJECT_SEARCH = "https://geo.ngu.no/api/faktaark/nadag/sokGeotekniskUndersokelse.php?search=%(projectnr)s&limit=20&params="
URL_PROJECT_PAGE = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskUndersokelse.php?id=%(project_id)s"
URL_BOREHOLE_LIST = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskUndersokelseBorehull.php?id=%(project_id)s"
URL_BOREHOLE_INFO = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskBorehull.php?id=%(borehole_id)s"

WFS_SERVER = "https://geo.ngu.no/geoserver/nadag/wfs"
CRS = 'EPSG:25833'
FEATURE_TYPE = 'nadag:GB_borefirma'
SGF_EXTENSIONS = ["tot", "cpt", "std"]

def get_project_ids_from_bounds(bounds):
    """Look up project id:s using a geographical bounding box.

    bounds is (minx, miny, maxx, maxy) in crs 25833

    Returns a dictionary of {project_id: projectnr}
    """
    wfs11 = WebFeatureService(url=WFS_SERVER, version='2.0.0')

    # Removed from use for version 1.0.0 WFS server
    #c = crs.Crs(CRS)
    #srsname = c.getcodeurn()

    response = wfs11.getfeature(typename=FEATURE_TYPE, bbox=bounds)
    data = lxml.etree.parse(response)

    def get_name(project):
        names = project.xpath(".//nadag:prosjektnr/text()", namespaces={'nadag': 'https://geo.ngu.no/nadag'})
        if names: return names[0]
        names = project.xpath(".//nadag:prosjektnavn/text()", namespaces={'nadag': 'https://geo.ngu.no/nadag'})
        if names: return names[0]
        return "[Unknown]"
    
    return {project.xpath(".//nadag:opprinneliggeotekniskundersid/text()", namespaces={'nadag': 'https://geo.ngu.no/nadag'})[0]:
            get_name(project)
            for project in data.xpath("//nadag:GB_borefirma", namespaces={'nadag': 'https://geo.ngu.no/nadag'})}

def get_project_id(projectnr):
    """Look up a project_id using a projectnr (as specified by the
    uploading user)"""
    oriprojectnr = projectnr
    status = None
    while projectnr:
        r = session.get(URL_PROJECT_SEARCH % {"projectnr": projectnr}).json()
        status = r["status"]
        if r["status"]["success"] == "true" and r["status"]["hits"] >= 1:
            return r["content"][0]["lokalid"]
        if "-" not in projectnr:
            break
        projectnr = projectnr.rsplit("-", 1)[0]
    raise Exception("Unable to find %s: %s" % (oriprojectnr, status))

def _get_info(table):
    def get_value(value):
        if len(value.find("a")):
            return {a.text: list(a.absolute_links)[0]
                    for a in value.find("a")}
        return value.text
    return {list(set(tr.find("td")[0].attrs["class"]) - set(['header']))[0]: get_value(tr.find(".value")[0])
            for tr in table.find("tr")}

def get_project_info(project_id):
    r = session.get(URL_PROJECT_PAGE % {"project_id": project_id})
    return _get_info(r.html.find("table")[0])

def get_project_boreholes(project_id):
    """Get a dictionary of project metadata given a project_id""" 
    def extract_borehole_id(url):
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["id"][0]
    r = session.get(URL_BOREHOLE_LIST % {"project_id": project_id})
    return {tr.find("td")[0].text: extract_borehole_id(list(tr.absolute_links)[0])
            for tr in r.html.find("tr")
            if len(tr.links)}

def get_borehole_info(borehole_id):
    """Get a dictionary of borehole metadata given a borehole_id"""
    r = session.get(URL_BOREHOLE_INFO % {"borehole_id": borehole_id})
    return _get_info(r.html.find("table")[0])

def _get_project_zip_files(project_info):
    return {v for k, v in project_info["report"].items() if k.lower().endswith(".zip")}

def get_project_borehole_data(project_id):
    """Download & parse all borehole data for a project. Data returned
    uses the same datamodel as libsgfdata, except that the toplevel is not
    a list of boreholes, but a dictionary of borehole_id: borehole_data.

        list(get_project_borehole_data(project_id).values())

    will get you a fully libsgfdata compatible data structure.
    """
    
    borehole_map = get_project_boreholes(project_id)
    res = {}
    for url in _get_project_zip_files(get_project_info(project_id)):
        r = session.get(url)
        zipf = zipfile.ZipFile(io.BytesIO(r.content))
        for name in zipf.namelist():
            ext = name.lower().split(".")[-1] if "." in name else ""
            if ext in SGF_EXTENSIONS:
                try:
                    data = libsgfdata.parse(zipf.open(name))
                except Exception as e:
                    logger.warn("Unable to parse %s:%s: %s" % (url, name, e))
                    continue
                for section in data:
                    if "main" not in section or not len(section["main"][0]) or "investigation_point" not in section["main"][0]:
                        continue
                    investigation_point = str(section["main"][0]["investigation_point"])
                    if investigation_point not in borehole_map:
                        continue
                    borehole_id = borehole_map[investigation_point]
                    section["nadag"] = get_borehole_info(borehole_id)

                    # Map some nadag attributes to the corresponding SGF ones
                    x, y = [float(c.split(":")[0]) for c in section["nadag"]["koord"].split(" ")]
                    z = float(section["nadag"]["hoeyde"].split(" ")[0])
                    section["main"][0]["x_coordinate"] = x
                    section["main"][0]["y_coordinate"] = y
                    section["main"][0]["z_coordinate"] = z
                    
                    res[borehole_id] = section
    return res
