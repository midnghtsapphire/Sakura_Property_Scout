import json, os
from pathlib import Path
import psycopg

DB=os.environ['NEON_DATABASE_URL']
out=Path('data'); out.mkdir(exist_ok=True)

SQL={
'properties.json': '''SELECT jsonb_agg(jsonb_build_object('id',p.property_id,'address',p.address,'market',p.city||', '||p.state,'type',p.property_type,'price',p.asking_price,'lotRent',p.lot_rent_monthly,'landOwned',p.land_owned,'beds',p.bedrooms,'baths',p.bathrooms,'sqft',p.sqft,'yearBuilt',p.year_built,'status',p.data_status,'source',p.listing_source,'sourceChecked',to_char(p.source_checked_at,'YYYY-MM-DD'),'url',p.listing_url,'note',p.notes) ORDER BY p.asking_price,p.property_id) FROM properties p''',
'grants.json': '''SELECT jsonb_agg(jsonb_build_object('id',g.grant_id,'name',g.name,'agency',g.agency,'geography',g.geography,'programType',g.program_type,'maxAmount',g.max_amount,'fundingForm',g.funding_form,'applicationStatus',g.application_status,'dataStatus',g.data_status,'verifiedAt',to_char(g.verified_at,'YYYY-MM-DD'),'url',g.program_url,'note',COALESCE(g.stacking_notes,g.notes)) ORDER BY g.application_status DESC,g.geography,g.name) FROM grants g''',
'intelligence.json': '''SELECT jsonb_agg(jsonb_build_object('propertyId',p.property_id,'address',p.address,'score',jsonb_build_object('overall',s.overall_score,'confidence',s.evidence_confidence,'bones',s.bones_score,'water',s.water_score,'terrain',s.terrain_score,'greenery',s.greenery_score,'walkability',s.walkability_score,'adventure',s.adventure_score,'grant',s.grant_score,'tornadoRisk',s.tornado_risk,'floodRisk',s.flood_risk,'wildfireRisk',s.wildfire_risk,'trip',s.trip_recommendation),'rentals',COALESCE((SELECT jsonb_agg(jsonb_build_object('strategy',r.strategy,'status',r.allowed_status,'url',r.rules_source_url,'notes',r.notes) ORDER BY r.strategy) FROM rental_scenarios r WHERE r.property_id=p.property_id),'[]'::jsonb),'nearby',COALESCE((SELECT jsonb_agg(jsonb_build_object('name',n.place_name,'type',n.place_type,'miles',n.distance_miles,'driveMin',n.drive_minutes,'walkMin',n.walk_minutes,'url',n.source_url,'notes',n.notes) ORDER BY n.place_name) FROM nearby_places n WHERE n.property_id=p.property_id),'[]'::jsonb),'rehab',COALESCE((SELECT jsonb_agg(jsonb_build_object('category',h.category,'severity',h.severity,'diy',h.diy_possible,'critical',h.critical_before_purchase,'notes',h.notes) ORDER BY h.critical_before_purchase DESC,h.category) FROM rehab_items h WHERE h.property_id=p.property_id),'[]'::jsonb)) ORDER BY p.asking_price,p.property_id) FROM properties p LEFT JOIN property_scores s ON s.property_id=p.property_id'''
}

with psycopg.connect(DB) as conn:
    with conn.cursor() as cur:
        for name,sql in SQL.items():
            cur.execute(sql)
            payload=cur.fetchone()[0] or []
            (out/name).write_text(json.dumps(payload,indent=2,default=str)+'\n',encoding='utf-8')
print('Exported Neon snapshots to data/')
