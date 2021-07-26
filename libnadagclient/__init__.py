import requests_html
import urllib.parse
import zipfile
import io
import libsgfdata

session = requests_html.HTMLSession()

URL_PROJECT_SEARCH = "https://geo.ngu.no/api/faktaark/nadag/sokGeotekniskUndersokelse.php?search=%(projectnr)s&limit=20&params="
URL_PROJECT_PAGE = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskUndersokelse.php?id=%(project_id)s"
URL_BOREHOLE_LIST = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskUndersokelseBorehull.php?id=%(project_id)s"
URL_BOREHOLE_INFO = "https://geo.ngu.no/api/faktaark/nadag/visGeotekniskBorehull.php?id=%(borehole_id)s"

def get_project_id(projectnr):
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
    def extract_borehole_id(url):
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["id"][0]
    r = session.get(URL_BOREHOLE_LIST % {"project_id": project_id})
    return {tr.find("td")[0].text: extract_borehole_id(list(tr.absolute_links)[0])
            for tr in r.html.find("tr")
            if len(tr.links)}

def get_borehole_info(borehole_id):
    r = session.get(URL_BOREHOLE_INFO % {"borehole_id": borehole_id})
    return _get_info(r.html.find("table")[0])

def _get_project_zip_files(project_info):
    return {v for k, v in project_info["report"].items() if k.lower().endswith(".zip")}

def get_project_borehole_data(project_id):
    borehole_map = get_project_boreholes(project_id)
    res = {}
    for url in _get_project_zip_files(get_project_info(project_id)):
        r = session.get(url)
        zipf = zipfile.ZipFile(io.BytesIO(r.content))
        for name in zipf.namelist():
            if name.lower().endswith(".tot") or name.lower().endswith(".cpt"):
                data = libsgfdata.parse(zipf.open(name))
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
