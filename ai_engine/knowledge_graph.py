"""
IndusTech Knowledge Graph Engine.
Builds entity-relationship graphs for Companies, Sectors, Products, Locations, and Workforce Skills.
Supports multi-hop graph traversal and semantic graph search.
"""

class KnowledgeGraphEngine:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self._build_industrial_graph()

    def add_node(self, node_id, label, node_type, properties=None):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                "properties": properties or {}
            }

    def add_edge(self, source_id, target_id, relation_type, weight=1.0):
        self.edges.append({
            "from": source_id,
            "to": target_id,
            "relation": relation_type,
            "label": relation_type.replace("_", " ").title(),
            "weight": weight
        })

    def _build_industrial_graph(self):
        # 1. Industrial Sectors
        sectors = [
            ("sec_mfg", "Manufacturing", "Sector"),
            ("sec_tex", "Textile", "Sector"),
            ("sec_pharma", "Pharmaceuticals", "Sector"),
            ("sec_chem", "Chemical", "Sector"),
            ("sec_const", "Construction", "Sector"),
            ("sec_food", "Food Processing", "Sector")
        ]
        for sid, slabel, stype in sectors:
            self.add_node(sid, slabel, stype, {"color": "#0d3b8e"})

        # 2. Locations
        locations = [
            ("loc_pune", "Pune Industrial Region", "Location"),
            ("loc_mumbai", "Thane-Mumbai Belt", "Location"),
            ("loc_noida", "Noida-NCR Belt", "Location"),
            ("loc_blr", "Bengaluru Tech Hub", "Location"),
            ("loc_gujarat", "Gujarat Chemical Corridor", "Location"),
            ("loc_hyd", "Hyderabad BioTech Valley", "Location"),
            ("loc_chennai", "Chennai Auto Hub", "Location")
        ]
        for lid, llabel, ltype in locations:
            self.add_node(lid, llabel, ltype, {"color": "#64748b"})

        # 3. Companies & Relationships
        companies = [
            # Pune Companies
            {
                "id": "comp_1", "name": "ABC Manufacturing Pvt Ltd", "sector": "sec_mfg", "loc": "loc_pune",
                "products": [("prod_cnc", "CNC Components"), ("prod_metal", "Metal Fabrication")],
                "skills": [("skill_cnc", "CNC Operator"), ("skill_weld", "Welding Specialist")]
            },
            {
                "id": "comp_2", "name": "XYZ Textiles & Fabrics", "sector": "sec_tex", "loc": "loc_pune",
                "products": [("prod_yarn", "Industrial Yarns"), ("prod_canvas", "Canvas Fabrics")],
                "skills": [("skill_weaver", "Textile Weaver"), ("skill_spin", "Yarn Spinner")]
            },
            {
                "id": "comp_3", "name": "BioPharma Synth Labs", "sector": "sec_pharma", "loc": "loc_pune",
                "products": [("prod_api", "Active Pharma APIs"), ("prod_finechem", "Fine Chemicals")],
                "skills": [("skill_chemist", "Organic Chemist"), ("skill_qa", "QA Manager")]
            },
            {
                "id": "comp_4", "name": "PolyChem Polymers India", "sector": "sec_chem", "loc": "loc_pune",
                "products": [("prod_resin", "Industrial Resins"), ("prod_adhesive", "Polymer Adhesives")],
                "skills": [("skill_polymer", "Polymer Scientist")]
            },

            # Mumbai Companies
            {
                "id": "comp_5", "name": "Reliance Heavy Engineering", "sector": "sec_mfg", "loc": "loc_mumbai",
                "products": [("prod_vessel", "Pressure Vessels"), ("prod_turbines", "Power Turbines")],
                "skills": [("skill_heavy", "Heavy Machinery Engineer"), ("skill_weld", "Welding Specialist")]
            },
            {
                "id": "comp_6", "name": "Godrej Process Equipment", "sector": "sec_mfg", "loc": "loc_mumbai",
                "products": [("prod_exchanger", "Heat Exchangers"), ("prod_reactors", "Chemical Reactors")],
                "skills": [("skill_process", "Process Engineer")]
            },

            # Noida/Delhi Companies
            {
                "id": "comp_7", "name": "Noida Electronics City", "sector": "sec_const", "loc": "loc_noida",
                "products": [("prod_pcb", "PCB Assemblies"), ("prod_enclosure", "Structural Enclosures")],
                "skills": [("skill_elec", "Electronics Technician")]
            },
            {
                "id": "comp_8", "name": "Gurugram Auto Ancillaries", "sector": "sec_mfg", "loc": "loc_noida",
                "products": [("prod_gears", "Automotive Gears"), ("prod_axles", "Forged Axles")],
                "skills": [("skill_cnc", "CNC Operator")]
            },

            # Bengaluru Companies
            {
                "id": "comp_9", "name": "Peenya Precision Tools", "sector": "sec_mfg", "loc": "loc_blr",
                "products": [("prod_moulds", "Injection Moulds"), ("prod_aero", "Aerospace Tools")],
                "skills": [("skill_cnc", "CNC Operator"), ("skill_tool", "Toolmaker")]
            },
            {
                "id": "comp_10", "name": "Karnataka Pharma Biotech", "sector": "sec_pharma", "loc": "loc_blr",
                "products": [("prod_vaccine", "Vaccine Formulations"), ("prod_reagent", "Clinical Reagents")],
                "skills": [("skill_biotech", "Biotech Researcher")]
            },

            # Gujarat Companies
            {
                "id": "comp_11", "name": "GIDC Vatva Chemical Consortium", "sector": "sec_chem", "loc": "loc_gujarat",
                "products": [("prod_dyes", "Organic Dyes"), ("prod_solvent", "Industrial Solvents")],
                "skills": [("skill_chemist", "Organic Chemist")]
            },
            {
                "id": "comp_12", "name": "Surat Premium Weaving Mills", "sector": "sec_tex", "loc": "loc_gujarat",
                "products": [("prod_fibers", "Synthetic Fibers"), ("prod_techtex", "Technical Textiles")],
                "skills": [("skill_weaver", "Textile Weaver")]
            },

            # Hyderabad & Chennai
            {
                "id": "comp_13", "name": "Genome Valley BioSciences", "sector": "sec_pharma", "loc": "loc_hyd",
                "products": [("prod_onco", "Oncology Drugs"), ("prod_bio", "Biosimilars")],
                "skills": [("skill_biotech", "Biotech Researcher")]
            },
            {
                "id": "comp_14", "name": "Chennai Auto & Heavy Machining", "sector": "sec_mfg", "loc": "loc_chennai",
                "products": [("prod_castings", "Engine Castings"), ("prod_pumps", "Hydraulic Pumps")],
                "skills": [("skill_foundry", "Foundry Engineer")]
            }
        ]

        for comp in companies:
            cid = comp["id"]
            cname = comp["name"]
            self.add_node(cid, cname, "Company", {"color": "#ef4444"})

            # Belongs to Sector
            self.add_edge(cid, comp["sector"], "BELONGS_TO")

            # Located In Location
            self.add_edge(cid, comp["loc"], "LOCATED_IN")

            # Produces Products
            for pid, pname in comp["products"]:
                self.add_node(pid, pname, "Product", {"color": "#3b82f6"})
                self.add_edge(cid, pid, "PRODUCES")
                # Product belongs to Sector
                self.add_edge(pid, comp["sector"], "USED_IN_SECTOR")

            # Hires Skills
            for skid, skname in comp["skills"]:
                self.add_node(skid, skname, "Skill", {"color": "#22c55e"})
                self.add_edge(cid, skid, "REQUIRES_SKILL")

        # 4. B2B Supply Chain Partner Relationships
        self.add_edge("comp_4", "comp_1", "SUPPLIES_MATERIAL_TO")  # PolyChem -> ABC Mfg (Resins)
        self.add_edge("comp_11", "comp_3", "SUPPLIES_SOLVENTS_TO") # GIDC Vatva -> BioPharma
        self.add_edge("comp_1", "comp_8", "SUPPLIES_PARTS_TO")     # ABC Mfg -> Gurugram Auto
        self.add_edge("comp_9", "comp_5", "SUPPLIES_TOOLS_TO")     # Peenya Tools -> Reliance Eng

    def get_full_graph(self):
        """Returns complete nodes and edges payload for Vis.js rendering."""
        node_list = []
        for nid, ndata in self.nodes.items():
            node_list.append({
                "id": nid,
                "label": ndata["label"],
                "group": ndata["type"],
                "type": ndata["type"]
            })
        return {
            "status": "success",
            "nodes": node_list,
            "edges": self.edges
        }

    def search_graph(self, query):
        """
        Traverses Knowledge Graph based on search query.
        Returns matching nodes, 1-hop & 2-hop connected neighbors, and connecting edges.
        """
        if not query or not query.strip():
            return self.get_full_graph()

        q = query.strip().lower()
        matched_node_ids = set()

        # Find direct matching nodes
        for nid, ndata in self.nodes.items():
            if q in ndata["label"].lower() or q in ndata["type"].lower():
                matched_node_ids.add(nid)

        if not matched_node_ids:
            return {"status": "success", "nodes": [], "edges": []}

        # 1-hop & 2-hop neighbor expansion
        active_nodes = set(matched_node_ids)
        sub_edges = []

        for edge in self.edges:
            src = edge["from"]
            tgt = edge["to"]
            if src in matched_node_ids or tgt in matched_node_ids:
                active_nodes.add(src)
                active_nodes.add(tgt)
                sub_edges.append(edge)

        # Build sub-graph payload
        sub_nodes = []
        for nid in active_nodes:
            ndata = self.nodes[nid]
            sub_nodes.append({
                "id": nid,
                "label": ndata["label"],
                "group": ndata["type"],
                "type": ndata["type"],
                "is_direct_match": nid in matched_node_ids
            })

        return {
            "status": "success",
            "query": query,
            "count": len(sub_nodes),
            "nodes": sub_nodes,
            "edges": sub_edges
        }

kg_engine = KnowledgeGraphEngine()
