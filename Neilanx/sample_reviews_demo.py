# Demo sample reviews for onboarding
DEMO_REVIEWS = [
    {
        "review": "Fantastisk service och snabb leverans! Produkten kom inom 24 timmar och var exakt som beskrevet. Kommer definitivt att handla här igen.",
        "rating": 5,
        "källa": "Webbshop",
        "name": "Anna Lindberg",
        "date": "2024-09-10"
    },
    {
        "review": "Bra kvalitet på produkten men leveransen tog längre tid än väntat. Kundtjänsten var dock mycket hjälpsam när jag kontaktade dem.",
        "rating": 4,
        "källa": "E-post",
        "name": "Erik Johansson",
        "date": "2024-09-09"
    },
    {
        "review": "Produkten var okej men inte riktigt vad jag förväntade mig baserat på beskrivningen. Prisvärd dock.",
        "rating": 3,
        "källa": "Google Reviews",
        "name": "Maria Svensson",
        "date": "2024-09-08"
    },
    {
        "review": "Utmärkt kundservice! Jag hade problem med min beställning och de löste det direkt. Mycket professionellt bemötande.",
        "rating": 5,
        "källa": "Trustpilot",
        "name": "Lars Pettersson",
        "date": "2024-09-07"
    },
    {
        "review": "Snabb leverans och bra förpackning. Produkten höll hög kvalitet och fungerade perfekt direkt ur lådan.",
        "rating": 5,
        "källa": "Webbshop",
        "name": "Ingrid Andersson",
        "date": "2024-09-06"
    },
    {
        "review": "Lite besviken på produktkvaliteten. Höll inte vad jag förväntade mig för det priset. Returen gick dock smidigt.",
        "rating": 2,
        "källa": "E-post",
        "name": "Johan Berg",
        "date": "2024-09-05"
    },
    {
        "review": "Första intrycket var mycket bra. Enkel beställningsprocess och tydlig kommunikation genom hela köpet.",
        "rating": 4,
        "källa": "Formulär",
        "name": "Cecilia Nilsson",
        "date": "2024-09-04"
    },
    {
        "review": "Rekommenderar starkt! Allt fungerade smidigt från beställning till leverans. Produkten överträffade mina förväntningar.",
        "rating": 5,
        "källa": "Google Reviews",
        "name": "Thomas Karlsson",
        "date": "2024-09-03"
    },
    {
        "review": "Okej produkt men webbsidan kunde vara mer användarvänlig. Svårt att hitta information om leveranstider.",
        "rating": 3,
        "källa": "Webbshop",
        "name": "Helena Ström",
        "date": "2024-09-02"
    },
    {
        "review": "Mycket nöjd med både produkt och service. Snabb leverans och produkten fungerar precis som utlovat. Toppbetyg!",
        "rating": 5,
        "källa": "Trustpilot",
        "name": "Mikael Lundgren",
        "date": "2024-09-01"
    }
]

def get_demo_reviews():
    """Return demo reviews for onboarding experience"""
    return DEMO_REVIEWS

def get_demo_csv_content():
    """Return demo reviews formatted as CSV string"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['review', 'rating', 'källa', 'name', 'date'])
    
    # Write data
    for review in DEMO_REVIEWS:
        writer.writerow([
            review['review'],
            review['rating'],
            review['källa'],
            review['name'],
            review['date']
        ])
    
    return output.getvalue()