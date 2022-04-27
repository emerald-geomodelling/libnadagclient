import libnadagclient
import re
import logging

def turn_on_logging():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

uuid_re = re.compile(r"\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b")
bbox_re = re.compile(r"[^0-9.]")

def parse_project(project_id_or_nr):
    turn_on_logging()
    if not re.match(uuid_re, project_id_or_nr):
        project_id_or_nr = libnadagclient.get_project_id(project_id_or_nr)
    d = libnadagclient.get_project_borehole_data(project_id_or_nr)
    return list(d.values())

def parse_bbox(bbox):
    turn_on_logging()
    bbox = [float(item) for item in re.split(bbox_re, bbox)]
    return [section
            for project in libnadagclient.get_project_ids_from_bounds(bbox)
            for section in libnadagclient.get_project_borehole_data(project).values()]
