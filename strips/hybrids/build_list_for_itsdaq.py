import argparse
import json
import os
import sys

if __name__ == '__main__':
    from __path__ import updatePath
    updatePath()

import itk_pdb.dbAccess as dbAccess

if os.getenv("ITK_DB_AUTH"):
    dbAccess.token = os.getenv("ITK_DB_AUTH")

# Primarily interested in ABC, HCC and AMAC
# Need to also keep the intermediated children to find these
interesting_child_types = ["ABC", "AMAC", "HCC", "HYBRID_ASSEMBLY", "MODULE", "PWB"]

# The top level things itsdaq is interested in
top_codes = ["MODULE", "HYBRID_ASSEMBLY"]

verbose = False

# Get fuse ID info from full component info
def get_fuse_id(comp):
    prop_names = {
        "ABC": "ID",
        "HCC": "EFUSE_HEX",
        "AMAC": "EFUSEID"
    }

    type_code = comp['componentType']['code']

    if type_code not in prop_names.keys():
        return None

    prop_name = prop_names[type_code]

    for p in comp['properties']:
        if p['code'] == prop_name:
            return p['value']

    return None

def list_components(institute, comp_types = None, cache = None):
    if cache is not None:
        comp_list = []
        for k in cache.list_all("list_full"):
            finfo = cache.fetch(k, "list_full")
            if comp_types is None:
                comp_list.append(finfo)
            elif finfo["componentType"]["code"] in comp_types:
                comp_list.append(finfo)
        return comp_list

    data = {
        "filterMap": {},
        "outputType": "full" # object is shorter, but need quite a lot of the info
    }

    # Ignore deleted and requested to delete
    data["filterMap"]["state"] = ["ready"]
    data["filterMap"]["trashed"] = False

    if institute is not None:
        data["filterMap"]["currentLocation"] = institute

    if comp_types is not None:
        data["filterMap"]["componentType"] = comp_types

    components = dbAccess.doSomething(action = 'listComponents',
                                      method = 'GET', data = data)

    if components["pageInfo"]["total"] == components["pageInfo"]["pageSize"]:
        # Maybe that many ABCs, but not hybrids at one site?
        print("Listing %s returned %d entries!" % (comp_types, components["pageSize"]))
        print(" This is too many to think about, so I'm giving up")
        sys.exit(1)

    # New API returns itemList, not pageItemList
    comp_list = components['itemList']

    return comp_list

def summarise_child_for_relationship(item):
    s = {}
    s['code'] = item['component']['code']
    s['serialNumber'] = item['component']['serialNumber']
    s['type_name'] = item['componentType']['name']
    s['type_code'] = item['componentType']['code']

    return s

def summarise_parent_for_relationship(item):
    s = {}
    s['code'] = item['code']
    s['serialNumber'] = item['serialNumber']
    s['type_name'] = item['componentType']['name']
    s['type_code'] = item['componentType']['code']

    return s

def get_component_data(component_list, cache):
    if cache is not None:
        return [cache.fetch(comp_id, "get_full") for comp_id in component_list]

    data = {"component": component_list}
    # Defaults to full output
    o = dbAccess.doSomething(action = 'getComponentBulk', method='get', data=data)
    return o["itemList"]

def summarise_relations(o):
    p = o['parents']
    c = o['children']
    parents = []
    children = []
    if p:
        for item in p:
            if item is None: continue
            if "code" in item and item['code'] is not None:
                parents.append(summarise_parent_for_relationship(item))
    if c:
        for item in c:
            if item is None: continue
            if "component" in item and item['component'] is not None:
                children.append(summarise_child_for_relationship(item))
    return parents, children

def summarise_from_full(comp):
    ci = {}

    ci['type'] = {
        'type': comp['componentType']['name'],
        'type_code': comp['componentType']['code'],
        'subtype': comp['type']['name'],
        'subtype_code': comp['type']['code']
    }

    ci['component'] = {
        'code': comp['code'],
        'SN': comp['serialNumber']
    }
    # ci['id'] = comp['id']

    fuse = get_fuse_id(comp)
    if fuse is not None:
        ci['component']['fuseID'] = fuse

    if comp['alternativeIdentifier'] is not None:
        ci['component']['alternativeIdentifier'] = comp['alternativeIdentifier']

    if comp['dummy']:
        ci['dummy'] = comp['dummy']

    return ci

class ComponentStore:
    """Store of information from DB for each component"""

    def __init__(self):
        # Full information from DB of requested components
        self.component_info = {}

    def store(self, code, info_type, info):
        cc = self.component_info.get(code, dict())
        cc[info_type] = info
        self.component_info[code] = cc

    def fetch(self, comp_id, info_type):
        if comp_id not in self.component_info:
            raise RuntimeError("Didn't know anything about %s" % comp_id)

        if info_type not in self.component_info[comp_id]:
            raise RuntimeError("Didn't have data (%s) for %s" % (info_type, comp_id))

        return self.component_info[comp_id][info_type]

    def list_all(self, info_type):
        return [k for (k, v) in self.component_info.items() if info_type in v]

    def load_cache(self):
        with open("itsdaq_component_info.json", "r") as f:
            self.component_info = json.load(f)

    def save_cache(self):
        with open("itsdaq_component_info_output.json", "w") as f:
            json.dump(self.component_info, f, indent=4)

def summarise_component(comp_code, store):
    try:
        comp_all = store.component_info[comp_code]
    except KeyError:
        print("No data for %s" % comp_code)
        return {"code": comp_code, "missing_data": True}

    comp_data = None
    for src in ["list_full", "get_full"]:
        try:
            comp_data = store.fetch(comp_code, src)
        except RuntimeError:
            pass

    if comp_data is None:
        print("Failed to get data for %s before summary" % comp_code)
        return {"code": comp_code, "available": comp_all}

    ci = summarise_from_full(comp_data)

    # "list_full" doesn't have info on parent/child
    rel_data = store.fetch(comp_code, "get_full")

    p, c = summarise_relations(rel_data)
    if len(p) > 0:
        ci['parents'] = p
    if len(c) > 0:
        ci['children'] = c

    return ci

def fetch_rels_data(need_rels_for, store, cache):
    have_data = store.list_all("get_full")

    need_list = [n for n in need_rels_for if n not in have_data]

    if len(need_rels_for) != len(need_list):
        print("Pruned list to: %s" % len(need_list))

    # More children
    need_rels = []

    # How many to get at once
    bulk_size = 5

    while len(need_list) > 0:
        fetch_list = need_list[:bulk_size]
        need_list[:bulk_size] = []

        if verbose:
            print("Fetching %s for rels" % fetch_list)
        else:
            print(".", end='')

        new_list = get_component_data(fetch_list, cache)

        for c in new_list:
            code = c["code"]
            store.store(code, "get_full", c)

            if c["children"] is None:
                continue

            # Add children to recurse
            for child_slot in c["children"]:
                if "component" in child_slot and child_slot["component"] is not None:
                    need_rels.append(child_slot["component"]["code"])

    if not verbose:
        print(" done")

    return need_rels

def follow_hierarchy(need_rels_for, store, cache):
    # Fetch data that's marked as needed
    print("Have %d components to follow relations for" % len(need_rels_for))
    limit_depth = 0

    while limit_depth < 6:
        limit_depth += 1

        next_layer = fetch_rels_data(need_rels_for, store, cache)
        if len(next_layer) == 0:
            break
        print("Need more info on %d children (depth %d)" % (len(next_layer), limit_depth))
        need_rels_for = next_layer

def main(institute, output_filename, testing):
    cache = None
    if testing:
        cache = ComponentStore()
        cache.load_cache()

    comp_list = list_components(institute, top_codes, cache)

    # Store components between passes of the loop
    cs = ComponentStore()

    need_rels = []

    # First load the data from the database into the store
    for comp in comp_list:
        # Ignore if trashed
        if comp['trashed']:
            continue

        code = comp["code"]

        cs.store(code, "list_full", comp)

        # Need more information on these
        need_rels.append(code)

    follow_hierarchy(need_rels, cs, cache)

    # Now take data from store to summarise for output
    output = []
    for comp in cs.component_info.keys():
        if verbose:
            print("Summarise %s" % comp)
        ci = summarise_component(comp, cs)
        output.append(ci)

    with open(output_filename, "w") as f:
        json.dump(output, f, indent=4)

    if testing:
        cs.save_cache()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read info for itsdaq from production database")
    parser.add_argument("--institute", help="Local institute code")
    parser.add_argument("--output", default="components.json", help="Output file name")
    parser.add_argument("--testing", default=False, action='store_true', help="Testing, using local file instead of DB")

    args = parser.parse_args()
    if args.institute is None:
        print("Required institute")
        sys.exit(1)
    else:
        print("Using institute %s" % args.institute)

    main(args.institute, args.output, args.testing)
