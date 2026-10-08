import os
import time
import pandas as pd
# pyrefly: ignore [missing-import]
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
def main():
    start_time = time.time()
    
    # Step 1: Connect to Neo4j
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    password = os.getenv("NEO4J_PASSWORD", "your_neo4j_password")
    
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))
    
    print("Connected to Neo4j.")
    
    def clear_db(tx):
        tx.run("MATCH (n) WHERE n:Company OR n:MIDCZone OR n:Industry DETACH DELETE n")

    with driver.session() as session:
        # Step 2: Clear existing nodes
        print("Clearing existing graph...")
        session.execute_write(clear_db)
        
        # Step 3: Load CSV
        print("Reading CSV...")
        df = pd.read_excel('Pune_MIDC_Companies_FINAL.xlsx')
        
        # Step 4: Create MIDCZone nodes
        print("Creating MIDCZone nodes...")
        def create_zone(tx, zone_name, lat, lng, count, top_industry):
            tx.run("""
                CREATE (z:MIDCZone {
                    name: $name, lat: $lat, lng: $lng, 
                    company_count: $count, dominant_industry: $top_industry
                })
            """, name=zone_name, lat=lat, lng=lng, count=count, top_industry=top_industry)

        zones = []
        for zone, group in df.groupby('midc_area'):
            if pd.isna(zone): continue
            lat = group['latitude'].mean()
            lng = group['longitude'].mean()
            count = len(group)
            top_industry = group['industry_label'].value_counts().index[0] if not group['industry_label'].empty else "Unknown"
            
            session.execute_write(create_zone, zone, float(lat) if pd.notna(lat) else 0.0, 
                                  float(lng) if pd.notna(lng) else 0.0, count, top_industry)
            zones.append(zone)

        # Step 5: Create Industry nodes
        print("Creating Industry nodes...")
        def create_industry(tx, name, count):
            tx.run("CREATE (i:Industry {name: $name, total_companies: $count})", 
                   name=name, count=count)
            
        industries = []
        for ind, group in df.groupby('industry_label'):
            if pd.isna(ind): continue
            session.execute_write(create_industry, ind, len(group))
            industries.append(ind)

        # Step 6 & 7: Create Company nodes and relationships in batches
        print("Creating Company nodes and relationships...")
        
        def create_companies_batch(tx, batch):
            query = """
            UNWIND $batch AS row
            CREATE (c:Company {
                name: row.company_name,
                address: row.address,
                business_type: row.business_type,
                lat: row.lat,
                lng: row.lng,
                rating: row.rating,
                total_reviews: row.total_reviews,
                website: row.website,
                phone: row.phone
            })
            WITH c, row
            MATCH (z:MIDCZone {name: row.midc_area})
            CREATE (c)-[:LOCATED_IN]->(z)
            WITH c, row
            MATCH (i:Industry {name: row.industry_label})
            CREATE (c)-[:BELONGS_TO]->(i)
            """
            tx.run(query, batch=batch)

        batch = []
        batch_size = 500
        for idx, row in df.iterrows():
            if pd.isna(row['company_name']): continue
            
            company_data = {
                "company_name": row['company_name'],
                "address": row['address'] if pd.notna(row['address']) else "",
                "business_type": row['business_type'] if pd.notna(row['business_type']) else "",
                "lat": float(row['latitude']) if pd.notna(row['latitude']) else 0.0,
                "lng": float(row['longitude']) if pd.notna(row['longitude']) else 0.0,
                "rating": float(row['rating']) if pd.notna(row['rating']) else 0.0,
                "total_reviews": int(row['total_reviews']) if pd.notna(row['total_reviews']) else 0,
                "website": row['website'] if pd.notna(row['website']) else "",
                "phone": row['phone'] if pd.notna(row['phone']) else "",
                "midc_area": row['midc_area'] if pd.notna(row['midc_area']) else "",
                "industry_label": row['industry_label'] if pd.notna(row['industry_label']) else ""
            }
            batch.append(company_data)
            
            if len(batch) >= batch_size:
                session.execute_write(create_companies_batch, batch)
                batch = []
        
        if batch:
            session.execute_write(create_companies_batch, batch)

        # Step 8: Create CONCENTRATED_IN relationships
        print("Creating CONCENTRATED_IN relationships...")
        def create_concentrated_in(tx, ind, zone, count, pct):
            tx.run("""
                MATCH (i:Industry {name: $ind})
                MATCH (z:MIDCZone {name: $zone})
                CREATE (i)-[:CONCENTRATED_IN {count: $count, percentage: $pct}]->(z)
            """, ind=ind, zone=zone, count=count, pct=pct)

        for ind, group in df.groupby('industry_label'):
            if pd.isna(ind): continue
            total_ind = len(group)
            zone_counts = group['midc_area'].value_counts()
            for zone, count in zone_counts.items():
                if pd.isna(zone): continue
                pct = float(count) / total_ind * 100
                session.execute_write(create_concentrated_in, ind, zone, int(count), pct)

        # Step 9: Create Neo4j indexes
        print("Creating indexes...")
        def create_indexes(tx):
            tx.run("CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)")
            tx.run("CREATE INDEX zone_name IF NOT EXISTS FOR (z:MIDCZone) ON (z.name)")
            tx.run("CREATE INDEX industry_name IF NOT EXISTS FOR (i:Industry) ON (i.name)")
        
        session.execute_write(create_indexes)
        
    driver.close()
    
    # Step 10: Summary
    print(f"✓ Created: {len(df)} Company nodes (approx)")
    print(f"✓ Created: {len(zones)} MIDCZone nodes")
    print(f"✓ Created: {len(industries)} Industry nodes")
    print("✓ Neo4j indexes created")
    print(f"Total time: {time.time() - start_time:.1f}s")

if __name__ == '__main__':
    main()
