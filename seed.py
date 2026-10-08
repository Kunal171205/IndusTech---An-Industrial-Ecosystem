from app import app
from database import db
from models import Worker, Company, JobPost, sellitem
from datetime import time, date

def seed_data():
    with app.app_context():
        # Clean existing data to avoid duplicates if re-run
        db.drop_all()
        db.create_all()

        print("Seeding Companies...")
        companies = [
            Company(
                company_name="ABC Manufacturing Pvt Ltd",
                email="contact@abc-mfg.com",
                password="password123",
                company_category="Manufacturing",
                company_size="150-200",
                company_city="Pune",
                founded_year=2010,
                gst_number="27ABCDE1234F1Z5",
                phone="9876543210",
                address="MIDC Pune",
                contact_person="Ramesh Patel",
                contact_designation="HR Manager"
            ),
            Company(
                company_name="XYZ Textiles",
                email="hr@xyztextiles.com",
                password="password123",
                company_category="Textile",
                company_size="500+",
                company_city="Aurangabad",
                founded_year=1995,
                gst_number="27FGHIJ5678K1Z2",
                phone="9876543211",
                address="MIDC Aurangabad",
                contact_person="Suresh Sharma",
                contact_designation="Director"
            ),
            Company(
                company_name="PharmaCure Industries",
                email="careers@pharmacure.com",
                password="password123",
                company_category="Pharma",
                company_size="50-100",
                company_city="Nashik",
                founded_year=2015,
                gst_number="27KLMNO9012P1Z3",
                phone="9876543212",
                address="MIDC Nashik",
                contact_person="Anita Desai",
                contact_designation="Plant Head"
            ),
            Company(
                company_name="BuildRight Construction",
                email="info@buildright.com",
                password="password123",
                company_category="Construction",
                company_size="200-500",
                company_city="Nagpur",
                founded_year=2008,
                gst_number="27PQRST3456U1Z4",
                phone="9876543213",
                address="MIDC Nagpur",
                contact_person="Vikram Singh",
                contact_designation="Operations Manager"
            ),
            Company(
                company_name="ChemTech Solutions",
                email="admin@chemtech.com",
                password="password123",
                company_category="Chemical",
                company_size="10-50",
                company_city="Chakan",
                founded_year=2018,
                gst_number="27UVWXY7890Z1Z5",
                phone="9876543214",
                address="MIDC Chakan",
                contact_person="Neha Gupta",
                contact_designation="Admin"
            ),
            Company(
                company_name="FreshPack Foods",
                email="contact@freshpack.com",
                password="password123",
                company_category="Food",
                company_size="100-150",
                company_city="Satara",
                founded_year=2012,
                gst_number="27ZABCD1234E1Z6",
                phone="9876543215",
                address="MIDC Satara",
                contact_person="Priya Kumar",
                contact_designation="HR Exec"
            )
        ]
        
        db.session.bulk_save_objects(companies)
        db.session.commit()

        # Fetch inserted companies to get their IDs
        inserted_companies = Company.query.all()
        c_dict = {c.company_name: c for c in inserted_companies}

        print("Seeding Jobs...")
        jobs = [
            JobPost(
                company_id=c_dict["ABC Manufacturing Pvt Ltd"].id,
                job_title="Machine Operator",
                job_type="Production Worker",
                city="Pune",
                specific_location="Plot 45, MIDC Bhosari",
                shift="Full Time",
                job_start_time=time(9, 0),
                job_end_time=time(18, 0),
                job_opening_no=15,
                salary="500",
                description="Looking for experienced CNC machine operators. Minimum 2 years experience required.",
                job_contact="9876543210",
                status="Active"
            ),
            JobPost(
                company_id=c_dict["XYZ Textiles"].id,
                job_title="Quality Checker",
                job_type="Helper",
                city="Aurangabad",
                specific_location="Sector 12, Waluj MIDC",
                shift="Full Time",
                job_start_time=time(8, 0),
                job_end_time=time(17, 0),
                job_opening_no=8,
                salary="450",
                description="Need helpers for quality checking of garments.",
                job_contact="9876543211",
                status="Active"
            ),
            JobPost(
                company_id=c_dict["PharmaCure Industries"].id,
                job_title="Packaging Assistant",
                job_type="Helper",
                city="Nashik",
                specific_location="Satpur MIDC",
                shift="Part Time",
                job_start_time=time(10, 0),
                job_end_time=time(14, 0),
                job_opening_no=20,
                salary="300",
                description="Packaging assistants needed for pharmaceutical products.",
                job_contact="9876543212",
                status="Active"
            ),
            JobPost(
                company_id=c_dict["BuildRight Construction"].id,
                job_title="Site Supervisor",
                job_type="Other",
                city="Nagpur",
                specific_location="Hingna MIDC",
                shift="Full Time",
                job_start_time=time(9, 30),
                job_end_time=time(18, 30),
                job_opening_no=5,
                salary="800",
                description="Experienced site supervisor required for new construction project.",
                job_contact="9876543213",
                status="Active"
            ),
            JobPost(
                company_id=c_dict["ChemTech Solutions"].id,
                job_title="Security Guard",
                job_type="Security",
                city="Chakan",
                specific_location="Phase 2, Chakan MIDC",
                shift="Full Time",
                job_start_time=time(20, 0),
                job_end_time=time(8, 0),
                job_opening_no=10,
                salary="600",
                description="Night shift security guards needed for chemical plant.",
                job_contact="9876543214",
                status="Active"
            ),
            JobPost(
                company_id=c_dict["FreshPack Foods"].id,
                job_title="Cleaning Staff",
                job_type="Housekeeping",
                city="Satara",
                specific_location="Additional MIDC",
                shift="Part Time",
                job_start_time=time(7, 0),
                job_end_time=time(11, 0),
                job_opening_no=12,
                salary="250",
                description="Morning shift cleaning staff required.",
                job_contact="9876543215",
                status="Active"
            )
        ]
        
        db.session.bulk_save_objects(jobs)
        db.session.commit()

        print("Seeding Workers...")
        workers = [
            Worker(
                name="Raju Rastogi",
                email="raju@test.com",
                password="password123",
                phone_no="8888888881",
                gender="Male",
                dob=date(1990, 5, 15),
                address="Pune City",
                languages="Hindi,Marathi",
                is_password_set=True
            ),
            Worker(
                name="Farhan Qureshi",
                email="farhan@test.com",
                password="password123",
                phone_no="8888888882",
                gender="Male",
                dob=date(1992, 8, 20),
                address="Nashik City",
                languages="Hindi,English",
                is_password_set=True
            )
        ]
        
        db.session.bulk_save_objects(workers)
        db.session.commit()
        
        print("Seeding Trade Items...")
        items = [
            sellitem(
                company_id=c_dict["ABC Manufacturing Pvt Ltd"].id,
                sell_name="Steel Sheets",
                sell_price=5000.0,
                sell_quantity=100,
                sell_description="High-quality stainless steel sheets.",
                sell_category="Raw Material",
                sell_image='["steel1.jpg"]'
            ),
            sellitem(
                company_id=c_dict["XYZ Textiles"].id,
                sell_name="Cotton Yarn",
                sell_price=2000.0,
                sell_quantity=500,
                sell_description="Premium cotton yarn for textile weaving.",
                sell_category="Textile",
                sell_image='["yarn1.jpg"]'
            ),
            sellitem(
                company_id=c_dict["ChemTech Solutions"].id,
                sell_name="Industrial Solvent",
                sell_price=1500.0,
                sell_quantity=50,
                sell_description="Industrial grade cleaning solvent.",
                sell_category="Chemicals",
                sell_image='["solvent.jpg"]'
            )
        ]

        db.session.bulk_save_objects(items)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()
