import pandas as pd
import json
import numpy as np
import faiss
import time
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def main():
    start_time = time.time()
    
    # Step 1: Read CSV
    print("Reading CSV...")
    df = pd.read_excel('Pune_MIDC_Companies_FINAL.xlsx')
    
    # Step 2: Generate documents
    docs = []
    midc_docs = []
    
    print("Generating documents...")
    for idx, row in df.iterrows():
        company_name = row.get('company_name', 'Not available')
        industry_label = row.get('industry_label', 'Not available')
        business_type = row.get('business_type', 'Not available')
        midc_area = row.get('midc_area', 'Not available')
        address = row.get('address', 'Not available')
        rating = row.get('rating')
        if pd.isna(rating): rating = 'Not available'
        total_reviews = row.get('total_reviews')
        if pd.isna(total_reviews): total_reviews = 'Not available'
        website = row.get('website', 'Not available')
        phone = row.get('phone', 'Not available')
        
        text = f"{company_name} is a {industry_label} company of type {business_type} located in {midc_area} MIDC area in Pune, Maharashtra. Their address is {address}. Google rating: {rating} out of 5 based on {total_reviews} reviews. Website: {website}. Phone: {phone}."
        
        docs.append(text)
        
        midc_docs.append({
            "text": text,
            "company_name": company_name if pd.notna(company_name) else "Not available",
            "midc_area": midc_area if pd.notna(midc_area) else "Not available",
            "industry_label": industry_label if pd.notna(industry_label) else "Not available",
            "business_type": business_type if pd.notna(business_type) else "Not available",
            "lat": float(row['latitude']) if pd.notna(row.get('latitude')) else None,
            "lng": float(row['longitude']) if pd.notna(row.get('longitude')) else None,
            "rating": float(row['rating']) if pd.notna(row.get('rating')) else None,
            "total_reviews": int(row['total_reviews']) if pd.notna(row.get('total_reviews')) else None,
            "website": website if pd.notna(website) else "Not available",
            "phone": phone if pd.notna(phone) else "Not available",
            "address": address if pd.notna(address) else "Not available"
        })
    
    # Step 3: Load model
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Step 4: Embed documents
    print(f"Embedding {len(docs)} companies...")
    embeddings = model.encode(docs, batch_size=256, show_progress_bar=True)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # Step 5: Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    # Step 6: Save files
    faiss.write_index(index, 'midc_index.faiss')
    
    with open('midc_docs.json', 'w') as f:
        json.dump(midc_docs, f, indent=2)
        
    # Sector zone map
    sector_zone_map = {}
    
    for industry, group in df.groupby('industry_label'):
        if pd.isna(industry):
            continue
            
        zone_counts = group['midc_area'].value_counts()
        total = len(group)
        
        top_zones = []
        for zone, count in zone_counts.head(3).items():
            if pd.isna(zone):
                continue
            zone_group = group[group['midc_area'] == zone]
            lat_mean = zone_group['latitude'].mean()
            lng_mean = zone_group['longitude'].mean()
            
            top_zones.append({
                "zone": zone,
                "count": int(count),
                "pct": float(count / total * 100),
                "lat": float(lat_mean) if pd.notna(lat_mean) else None,
                "lng": float(lng_mean) if pd.notna(lng_mean) else None
            })
            
        sector_zone_map[str(industry)] = top_zones
        
    with open('sector_zone_map.json', 'w') as f:
        json.dump(sector_zone_map, f, indent=2)
        
    # Step 7: Print summary
    print(f"✓ FAISS index saved: midc_index.faiss ({index.ntotal} vectors, {dim} dims)")
    print("✓ Documents saved: midc_docs.json")
    print("✓ Sector map saved: sector_zone_map.json")
    print(f"Total time: {time.time() - start_time:.1f}s")

if __name__ == '__main__':
    main()
