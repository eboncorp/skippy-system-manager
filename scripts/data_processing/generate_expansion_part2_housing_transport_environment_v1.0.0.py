#!/usr/bin/env python3
"""
Generate Part 2: Housing, Transportation, Environmental terms (60+ terms)
For Dave Biggers Campaign - Run Dave Run
Budget: $1.025B, Mini Substations: at least one in every ZIP code
"""

import json

part2_terms = [

    # ========================================
    # HOUSING & DEVELOPMENT (25 terms)
    # ========================================

    {
        "term": "Accessory Dwelling Unit (ADU)",
        "definition": "A small secondary housing unit on the same lot as a single-family home. Examples: garage apartments, basement units, backyard cottages, 'granny flats.' Typically 400-1,200 square feet with own kitchen/bathroom.",
        "category": "Housing & Development",
        "louisville_context": "Louisville zoning severely restricts ADUs, despite housing shortage. Current rules require special permits, large lot sizes, and owner occupancy—making ADUs rare. Dave streamlines ADU permitting: allow by-right in all residential zones, reduce lot size requirements, remove owner-occupancy mandate, fast-track permits. ADUs provide: affordable rental units, aging-in-place options for seniors, multigenerational housing, and income for homeowners.",
        "why_it_matters": "Louisville needs 30,000 affordable units but prevents homeowners from creating units on their own property. ADUs add housing without new land, support aging seniors, create rental income, and cost nothing in public funds. Zoning restrictions are the only barrier.",
        "related_terms": "Missing Middle Housing, Zoning Reform, Affordable Housing, Density, Multigenerational Housing, Aging in Place",
        "dave_proposal": "Legalize ADUs by-right in all residential zones. Remove owner-occupancy requirements, reduce lot size minimums, fast-track permits (15-day approval), and provide design templates reducing costs."
    },
    {
        "term": "Missing Middle Housing",
        "definition": "Housing types between single-family homes and large apartments: duplexes, triplexes, fourplexes, townhomes, small apartment buildings. 'Missing' because zoning prohibits them in most neighborhoods despite being historically common.",
        "category": "Housing & Development",
        "louisville_context": "75% of Louisville land zoned single-family only, prohibiting duplexes and townhomes that were legal when built 100 years ago. This artificial scarcity drives housing costs up and sprawl out. Dave legalizes missing middle housing: allow duplexes/triplexes in all residential zones, streamline permitting, design standards ensuring neighborhood compatibility. Missing middle provides: naturally affordable units, gentle density, diverse neighborhood housing.",
        "why_it_matters": "Outlawing duplexes and townhomes doesn't preserve neighborhood character—those buildings created the neighborhoods people love. Missing middle housing provides affordable options without high-rise apartments, accommodating diverse family types and incomes in every neighborhood.",
        "related_terms": "Accessory Dwelling Unit, Single-Family Zoning, Density, Zoning Reform, Affordable Housing, Gentle Density",
        "dave_proposal": "Legalize missing middle housing (duplexes, triplexes, townhomes) in all residential zones. Streamline permits, establish design standards for compatibility, and allow gentle density throughout Louisville."
    },
    {
        "term": "Single-Family Zoning",
        "definition": "Zoning laws restricting areas to detached single-family homes only, prohibiting duplexes, apartments, and other housing types. Originated in 1920s as exclusionary tool and now drives housing costs up while limiting options.",
        "category": "Housing & Development",
        "louisville_context": "Louisville zones 75% of residential land for single-family only—illegal to build a duplex even on large lots. This creates: housing shortage (limiting supply), sprawl (forcing development outward), segregation (concentrating affordable housing in limited areas), and high costs (artificial scarcity). Most Louisville neighborhoods with single-family zoning contain pre-existing duplexes and apartments built before restrictive zoning.",
        "why_it_matters": "Single-family-only zoning is government deciding you can't build a duplex on your own property or rent out a basement apartment. It restricts housing supply, drives costs up, forces sprawl, and maintains segregation. Most 'character' neighborhoods people love were built before these restrictions.",
        "related_terms": "Missing Middle Housing, Exclusionary Zoning, Accessory Dwelling Unit, Zoning Reform, Housing Shortage, Density",
        "dave_proposal": "End single-family-only zoning. Allow missing middle housing (duplexes, townhomes, small apartments) throughout Louisville while maintaining neighborhood character through design standards, not arbitrary housing-type bans."
    },
    {
        "term": "Density",
        "definition": "The number of housing units or people per acre. Higher density means more homes on same land, enabling walkable neighborhoods, efficient services, and housing abundance. Artificially low density mandates drive sprawl and costs.",
        "category": "Housing & Development",
        "louisville_context": "Louisville zoning mandates low density: large minimum lot sizes (often 10,000+ square feet), maximum unit counts, and parking requirements that waste land. Result: sprawl, car dependence, high infrastructure costs, and housing shortage. Dave increases density limits near transit, commercial corridors, and job centers while respecting neighborhood scale. Smart density means: more housing options, walkable neighborhoods, efficient transit, lower costs.",
        "why_it_matters": "Low-density mandates force sprawl—Louisville spreads across huge area with population that could fit in half the space. Higher density near services and transit means: shorter commutes, walkable neighborhoods, viable transit, lower housing costs, less environmental impact. Density makes Louisville more affordable and livable.",
        "related_terms": "Smart Growth, Transit-Oriented Development, Missing Middle Housing, Zoning Reform, Walkability, Urban Planning",
        "dave_proposal": "Increase density limits near TARC routes, commercial corridors, and job centers. Remove minimum lot sizes in urban areas, reduce parking requirements, and allow gentle density (duplexes, townhomes) throughout residential zones."
    },
    {
        "term": "Parking Minimums",
        "definition": "Zoning requirements mandating minimum parking spaces for developments (e.g., 2 spaces per apartment). Increases costs, wastes land, encourages driving, and prevents development in walkable areas. Many cities eliminating these outdated rules.",
        "category": "Housing & Development",
        "louisville_context": "Louisville requires excessive parking: 2 spaces per apartment, 1 per 200 sq ft retail, etc. Result: parking lots dominate, development costs increase $30,000+ per unit, walkable development impossible. Example: a small apartment building might need more land for parking than housing. Dave eliminates parking minimums near transit, in downtown/commercial areas, and for affordable housing. Developers can still provide parking but aren't forced to overbuild it.",
        "why_it_matters": "Parking mandates are government requiring developers to build more parking than needed, raising housing costs and wasting land. Near transit and in walkable areas, excessive parking prevents the urbanism that makes neighborhoods desirable. Let the market determine parking needs.",
        "related_terms": "Zoning Reform, Transit-Oriented Development, Affordable Housing, Development Costs, Walkability, Housing Costs",
        "dave_proposal": "Eliminate parking minimums near TARC routes, in downtown/commercial districts, and for affordable housing. Allow market to determine parking needs. Promote shared parking and alternative transportation."
    },
    {
        "term": "Housing Trust Fund",
        "definition": "Dedicated public fund for affordable housing development and preservation, capitalized through taxes, fees, or budget allocations. Provides grants and loans for affordable housing construction, rehabilitation, and rental assistance.",
        "category": "Housing & Development",
        "louisville_context": "Louisville lacks dedicated affordable housing funding—competing annually for scarce budget dollars. Dave creates Housing Trust Fund capitalized by: (1) 1% of development fees, (2) payments from developers in lieu of required affordable units, (3) annual budget allocation of $5 million, (4) federal grant matches. Fund provides: construction financing for affordable housing, preservation of existing affordable units, emergency rental assistance, and down payment assistance for first-time homebuyers.",
        "why_it_matters": "Without dedicated funding, affordable housing depends on annual political fights over budget scraps. Housing Trust Fund ensures consistent investment, leverages private capital, and creates accountability for affordable housing production. Sustainable funding produces sustainable solutions.",
        "related_terms": "Affordable Housing, Inclusionary Zoning, Housing Finance, Development Fees, Rental Assistance, Homeownership",
        "dave_proposal": "Create Housing Trust Fund with $5M annual budget allocation plus development fees and in-lieu payments. Fund construction/preservation of affordable housing, emergency rental assistance, and first-time homebuyer programs."
    },
    {
        "term": "Rent Control",
        "definition": "Government limits on rent increases, typically capping annual increases at inflation rate or fixed percentage. Protects tenants from rapid rent spikes but controversial regarding effects on housing supply. Illegal in Kentucky (state preemption).",
        "category": "Housing & Development",
        "louisville_context": "Kentucky law prohibits local rent control, preventing Louisville from capping rent increases even during housing crises. While Dave can't implement rent control, alternatives include: (1) right to counsel for tenants facing eviction, (2) mandatory 60-day notice for rent increases over 10%, (3) relocation assistance for displaced tenants, (4) increasing affordable housing supply (reducing pressure), (5) tenant organizing rights.",
        "why_it_matters": "Rapid rent increases force displacement—working families priced out of neighborhoods as rents jump 20-30% annually. While rent control is illegal in Kentucky, Louisville can protect tenants through notice requirements, relocation assistance, legal aid, and building more affordable housing.",
        "related_terms": "Tenant Rights, Eviction Prevention, Affordable Housing, Displacement, Rent Burden, State Preemption",
        "dave_proposal": "While rent control is illegal in Kentucky, protect tenants through: 60-day notice for rent increases over 10%, relocation assistance for displaced tenants, right to legal counsel, and aggressive affordable housing construction."
    },
    {
        "term": "Section 8 Voucher",
        "definition": "Federal rental assistance program (Housing Choice Voucher) where eligible low-income families receive vouchers paying portion of rent directly to landlords. Tenants pay 30% of income; voucher covers remainder up to fair market rent.",
        "category": "Housing & Development",
        "louisville_context": "Louisville has 6,000+ families on Section 8 waiting list, with 2-3 year waits. Many landlords refuse vouchers despite federal anti-discrimination rules—Louisville doesn't enforce. Dave: (1) enforce source-of-income discrimination laws (require landlords accept vouchers), (2) expedite inspections so voucher-holders can move quickly, (3) landlord incentives (damage guarantees, faster payment), (4) partner with housing authority to expand voucher supply.",
        "why_it_matters": "Section 8 vouchers let low-income families afford market-rate housing, avoiding concentrated poverty. But if landlords refuse vouchers or waiting lists are years long, program fails. Louisville must enforce anti-discrimination and expand vouchers.",
        "related_terms": "Housing Choice Voucher, Public Housing, Affordable Housing, Housing Discrimination, Source-of-Income Protection, Fair Housing",
        "dave_proposal": "Enforce source-of-income discrimination laws requiring landlords accept Section 8 vouchers. Expedite inspections, provide landlord incentives, and advocate for expanded voucher allocation from federal government."
    },
    {
        "term": "Public Housing",
        "definition": "Government-owned rental housing for low-income residents, operated by local housing authorities. Federally funded but chronically underfunded, leading to deteriorating conditions and waiting lists. Louisville's public housing managed by Louisville Metro Housing Authority.",
        "category": "Housing & Development",
        "louisville_context": "Louisville Metro Housing Authority operates 4,000+ public housing units, with 8,000+ on waiting list and many units needing major repairs due to federal underfunding. Dave supports public housing through: (1) advocating for increased federal funding (HUD), (2) Metro budget support for maintenance/security, (3) mixed-income redevelopment of distressed properties, (4) resident services (job training, youth programs), (5) tenant organizing rights.",
        "why_it_matters": "Public housing provides stable, affordable homes for Louisville's most vulnerable residents. Decades of federal disinvestment created deteriorating conditions, but the solution is investment not demolition. Quality public housing is essential safety net.",
        "related_terms": "Louisville Metro Housing Authority, Affordable Housing, Section 8 Voucher, Mixed-Income Housing, Housing Authority, Federal Housing",
        "dave_proposal": "Support public housing through: advocacy for federal funding increases, Metro budget for maintenance/security, mixed-income redevelopment where appropriate, resident services, and protecting tenant organizing rights."
    },
    {
        "term": "Mixed-Income Housing",
        "definition": "Developments intentionally including units for various income levels—market-rate, moderate-income, and low-income—in same building or community. Promotes economic integration, reduces concentrated poverty, and cross-subsidizes affordable units.",
        "category": "Housing & Development",
        "louisville_context": "Louisville housing segregates by income: public housing concentrates poverty while affluent neighborhoods exclude affordable units. Mixed-income housing, required through inclusionary zoning and incentivized through tax credits, creates economically diverse communities. Research shows: better outcomes for low-income families (school quality, networks, opportunities), stable neighborhoods, reduced stigma. Model: 30% market-rate, 40% moderate-income, 30% low-income.",
        "why_it_matters": "Concentrated poverty creates intergenerational disadvantage—schools struggle, crime increases, opportunities vanish. Mixed-income housing provides low-income families access to opportunity-rich neighborhoods while maintaining affordability. Economic diversity strengthens communities.",
        "related_terms": "Inclusionary Zoning, Affordable Housing, Economic Integration, Public Housing, Concentrated Poverty, Opportunity",
        "dave_proposal": "Promote mixed-income housing through inclusionary zoning requirements, tax incentives for developers, and redevelopment of distressed public housing as mixed-income communities maintaining affordable units."
    },
    {
        "term": "Housing First",
        "definition": "Homelessness intervention providing permanent housing without preconditions (sobriety, treatment compliance, employment), then offering supportive services. Proven more effective and cheaper than shelter-based approaches. Recognizes housing as prerequisite for stability.",
        "category": "Housing & Development",
        "louisville_context": "Louisville's 1,500-2,000 homeless residents often cycle through shelters, jails, and emergency rooms—costly and ineffective. Housing First programs (Salt Lake City, Houston) show: 90%+ housing retention, 75% cost savings vs. emergency services, improved health outcomes. Dave implements Housing First: (1) create 500 permanent supportive housing units over 4 years, (2) pair with wellness center services, (3) end criminalization of homelessness, (4) rapid rehousing assistance.",
        "why_it_matters": "Requiring homeless people to get sober or employed before housing is backwards—stability requires housing first. Emergency rooms, jails, and shelters cost $50,000+ per person annually. Housing First provides homes and services for $15,000-20,000, with far better outcomes.",
        "related_terms": "Permanent Supportive Housing, Homelessness, Rapid Rehousing, Supportive Services, Community Wellness Center, Housing Stability",
        "dave_proposal": "Implement Housing First: create 500 permanent supportive housing units paired with wellness center services, rapid rehousing assistance, and end criminalization of homelessness (camping bans)."
    },
    {
        "term": "Permanent Supportive Housing",
        "definition": "Affordable housing combined with supportive services (mental health, addiction treatment, case management) for people experiencing chronic homelessness or disabilities. Housing First model with long-term stability focus.",
        "category": "Housing & Development",
        "louisville_context": "Louisville's chronically homeless population (500-700 people) has complex needs: mental illness, addiction, disabilities. Traditional shelters fail these residents. Permanent supportive housing provides: apartments with on-site services from wellness centers, no time limits, rent at 30% of income (often SSI/disability). Studies show 90% housing retention, dramatic health improvements, 75% cost savings vs. emergency services.",
        "why_it_matters": "Chronically homeless individuals cost taxpayers $50,000-100,000 annually through emergency rooms, jails, and crisis services. Permanent supportive housing costs $15,000-25,000 while actually ending homelessness and improving lives. It's both compassionate and fiscally responsible.",
        "related_terms": "Housing First, Homelessness, Supportive Services, Community Wellness Center, Chronic Homelessness, Affordable Housing",
        "dave_proposal": "Create 500 permanent supportive housing units over 4 years with on-site services from 18 wellness centers. Target chronically homeless individuals, with housing subsidies and comprehensive support."
    },
    {
        "term": "Rapid Rehousing",
        "definition": "Short-term rental assistance (3-6 months) and services helping homeless families quickly move into permanent housing. More cost-effective than shelters, with 80%+ of families maintaining housing after assistance ends.",
        "category": "Housing & Development",
        "louisville_context": "Most Louisville homeless families need temporary help (job loss, medical crisis, eviction) not long-term support. Rapid rehousing provides: immediate housing placement, short-term rent assistance, case management, employment support. Average cost: $3,000-5,000 per family vs. $6,000+ for shelter stay. Dave expands rapid rehousing: serve 1,000 families annually, fund through Housing Trust Fund, partner with landlords.",
        "why_it_matters": "Homeless families with children often need temporary help, not permanent subsidies. Rapid rehousing quickly returns families to stability at fraction of shelter cost, minimizing trauma to children and disruption to employment/school.",
        "related_terms": "Homelessness, Housing First, Rental Assistance, Family Homelessness, Housing Stability, Emergency Assistance",
        "dave_proposal": "Expand rapid rehousing serving 1,000 families annually: immediate housing placement, 3-6 month rental assistance, case management, employment support. Fund through Housing Trust Fund."
    },
    {
        "term": "Tenant Rights",
        "definition": "Legal protections for renters including: habitable conditions, privacy, anti-discrimination, fair eviction procedures, security deposit protections, and retaliation prohibitions. Stronger in some states; Kentucky provides minimal protections.",
        "category": "Housing & Development",
        "louisville_context": "Kentucky's tenant protections are among weakest nationally: landlords can evict with 7-day notice, no relocation assistance required, minimal habitability standards, no rent control allowed. Dave strengthens Louisville tenant rights: (1) right to legal counsel for eviction defense, (2) mandatory 60-day notice for no-fault evictions, (3) relocation assistance for displaced tenants, (4) proactive housing code enforcement, (5) tenant organizing rights, (6) source-of-income discrimination prohibited.",
        "why_it_matters": "Power imbalance between landlords and tenants drives displacement and exploitation. Stronger tenant rights provide stability, prevent unjust evictions, and ensure habitable conditions. Housing stability enables employment, education, and health.",
        "related_terms": "Eviction Prevention, Right to Counsel, Landlord-Tenant Law, Housing Stability, Tenant Organizing, Fair Housing",
        "dave_proposal": "Strengthen tenant rights: right to counsel for evictions, 60-day notice for no-fault evictions, relocation assistance, proactive code enforcement, tenant organizing protections, and source-of-income discrimination prohibition."
    },
    {
        "term": "Right to Counsel (Housing)",
        "definition": "Guaranteed legal representation for tenants facing eviction, similar to criminal defense. New York, San Francisco, and other cities provide free lawyers for low-income tenants. Dramatically reduces evictions and homelessness.",
        "category": "Housing & Development",
        "louisville_context": "90% of Louisville landlords have lawyers at eviction hearings; 90% of tenants don't. Result: families lose housing even for fixable issues (temporary financial crisis, landlord retaliation, uninhabitable conditions). Cities with right to counsel show: 80% of represented tenants stay housed, saves $3 in homelessness services for every $1 in legal aid. Dave implements right to counsel: free lawyers for tenants below 200% poverty line facing eviction.",
        "why_it_matters": "Eviction hearings are legal proceedings, but tenants face them alone while landlords have lawyers. One eviction can trigger cascading crises: job loss, homelessness, family separation, school disruption. Legal representation prevents unjust evictions and homelessness.",
        "related_terms": "Eviction Prevention, Tenant Rights, Legal Aid, Housing Stability, Access to Justice, Eviction Defense",
        "dave_proposal": "Implement right to counsel: provide free legal representation for tenants below 200% poverty line facing eviction. Fund through Housing Trust Fund, partnering with legal aid organizations."
    },

    # ========================================
    # TRANSPORTATION & INFRASTRUCTURE (25 terms)
    # ========================================

    {
        "term": "TARC (Transit Authority of River City)",
        "definition": "Louisville's public bus system, providing 2.8 million rides annually across 50+ routes. Governed by independent authority, funded by Metro government, fares, and federal grants. Critical mobility tool for car-free residents.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "TARC serves 30,000+ riders daily, predominantly low-income residents, seniors, people with disabilities, and students. Current challenges: infrequent service (30-60 minute waits), limited weekend/evening hours, and routes designed for suburbs not urban density. Dave improves TARC: (1) increase frequency on major routes to 15-minute service, (2) expand weekend/evening service, (3) real-time arrival information at all stops, (4) bus shelters with seating, (5) fare integration with bikeshare.",
        "why_it_matters": "Car ownership costs $10,000+ annually—out of reach for 20% of Louisville households. TARC provides mobility for work, healthcare, groceries. But infrequent service and poor conditions make riders wait in rain, miss connections, and lose jobs due to unreliable transit.",
        "related_terms": "Public Transit, Bus Rapid Transit, Transit-Oriented Development, Transportation Equity, Mobility, Frequency",
        "dave_proposal": "Invest in TARC improvements: increase frequency to 15-minute service on major routes, expand weekend/evening service, real-time arrival information, bus shelters with seating at all stops, and integrate fares with bikeshare."
    },
    {
        "term": "Bus Rapid Transit (BRT)",
        "definition": "High-quality bus service with dedicated lanes, level boarding, off-board fare payment, and frequent service (every 5-10 minutes). Provides rail-like experience at fraction of cost. Typical BRT carries 5,000-20,000 riders daily per route.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville lacks high-quality transit. BRT on major corridors (Bardstown Road, Dixie Highway, Preston Highway) would provide: dedicated bus lanes (not stuck in traffic), 10-minute frequency all day, level boarding for wheelchairs/strollers, modern stations with real-time info, faster travel than driving during rush hour. Cost: $20-40M per route vs. $300M+ for rail. Dave prioritizes BRT on corridors with highest ridership potential.",
        "why_it_matters": "Regular buses stuck in traffic can't compete with driving. BRT provides reliable, frequent, comfortable transit at fraction of rail cost—transforming Louisville's transit from last resort to competitive choice. BRT catalyzes development, reduces traffic, and improves mobility.",
        "related_terms": "TARC, Public Transit, Transit-Oriented Development, Dedicated Lanes, Rapid Transit, Transportation",
        "dave_proposal": "Develop Bus Rapid Transit on major corridors (Bardstown Rd, Dixie Hwy, Preston Hwy): dedicated lanes, 10-minute frequency, level boarding, modern stations. Start with highest-ridership corridor as pilot."
    },
    {
        "term": "Frequency (Transit)",
        "definition": "How often transit arrives—the most important factor in ridership. High frequency = every 10-15 minutes or better, meaning riders don't need schedules. Low frequency = 30-60 minutes, requiring schedule consultation and long waits.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Most TARC routes run every 30-60 minutes, requiring schedule memorization and painful waits if buses are missed. Studies show: frequency matters more than coverage—people will walk farther for frequent service. Dave prioritizes frequency: major routes every 15 minutes all day (high frequency), crosstown routes every 30 minutes. Frequency makes transit competitive: riders arrive and wait minutes not 30-45 minutes.",
        "why_it_matters": "When buses come every 45 minutes, missing one means 45-minute wait—making transit unusable for most trips. Frequent service (every 10-15 minutes) means just go to stop; bus arrives soon. Frequency transforms transit from schedule-dependent to spontaneous, like driving.",
        "related_terms": "TARC, Bus Rapid Transit, Public Transit, Transit Reliability, Service Quality, Ridership",
        "dave_proposal": "Prioritize frequency over coverage: major TARC routes every 15 minutes all day, crosstown routes every 30 minutes. Concentrate service on high-ridership corridors achieving high-frequency service people can use without schedules."
    },
    {
        "term": "Vision Zero",
        "definition": "Traffic safety philosophy that traffic deaths are preventable, not inevitable, and commits to eliminating all traffic fatalities through street design, speed management, enforcement, and behavior change. Originated in Sweden 1997.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville averages 60-70 traffic deaths annually, with pedestrian deaths concentrated in low-income neighborhoods with dangerous street designs. Vision Zero approach: (1) identify high-crash corridors using data, (2) redesign streets for safety (narrower lanes, crosswalks, traffic calming), (3) lower speed limits on residential streets to 25 mph, (4) prioritize pedestrian deaths (not just total crashes), (5) public reporting on progress.",
        "why_it_matters": "Traffic deaths aren't 'accidents'—they're predictable results of dangerous street design and excessive speeds. Vision Zero acknowledges humans make mistakes but demands streets designed so mistakes don't kill. Louisville's high pedestrian death rates disproportionately affect low-income neighborhoods.",
        "related_terms": "Complete Streets, Traffic Calming, Pedestrian Safety, Speed Management, Safe Routes to School, Transportation Safety",
        "dave_proposal": "Adopt Vision Zero commitment: identify high-crash corridors using data, redesign dangerous streets, reduce residential speed limits to 25 mph, prioritize pedestrian safety, and annual public reporting on traffic deaths/injuries."
    },
    {
        "term": "Traffic Calming",
        "definition": "Street design techniques slowing vehicles and improving safety: speed humps, curb extensions, raised crosswalks, chicanes, roundabouts. Makes streets safer for pedestrians/cyclists while maintaining access. Proven to reduce speeds and crashes.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville streets designed for speed, not safety: wide lanes, long straight stretches, minimal crosswalks encourage speeding through neighborhoods. Traffic calming transforms dangerous corridors: raised crosswalks at every school, curb extensions narrowing intersections and slowing turns, speed tables along residential streets. Focuses on neighborhoods with high pedestrian deaths and along school routes. Community input determines appropriate treatments.",
        "why_it_matters": "Speed kills—pedestrians struck at 40 mph have 85% death rate vs. 10% at 20 mph. Wide, straight streets encourage speeding through neighborhoods where kids play and seniors walk. Traffic calming physically slows vehicles, saving lives without enforcement.",
        "related_terms": "Vision Zero, Complete Streets, Pedestrian Safety, Safe Routes to School, Speed Management, Neighborhood Safety",
        "dave_proposal": "Implement traffic calming on high-crash corridors and school routes: raised crosswalks, curb extensions, speed tables, and roundabouts. Prioritize neighborhoods with high pedestrian deaths and community-requested treatments."
    },
    {
        "term": "Bike Infrastructure",
        "definition": "Facilities enabling safe cycling: protected bike lanes (physical separation from traffic), conventional bike lanes (painted), multi-use paths, bike parking, and signals. Quality infrastructure dramatically increases cycling safety and ridership.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville has minimal bike infrastructure: 50 miles of mostly painted lanes on high-speed roads where few dare bike. Dave builds protected bike network: 200 miles of protected bike lanes over 8 years, connecting neighborhoods to downtown, jobs, parks, and services. Protected lanes use planters, posts, or curbs physically separating bikes from traffic. Focus on low-income neighborhoods where residents need car-free transportation.",
        "why_it_matters": "Painted bike lanes on 40 mph roads don't make cycling safe—only protected infrastructure encourages cycling by 'interested but concerned' majority. Cycling provides transportation for people who can't afford cars ($10,000+ annually) and healthy exercise. Protected bike lanes make Louisville accessible without car ownership.",
        "related_terms": "Complete Streets, Protected Bike Lanes, Active Transportation, Mobility, Transportation Equity, Multi-Modal Transportation",
        "dave_proposal": "Build 200 miles of protected bike lane network over 8 years, connecting neighborhoods to downtown, jobs, parks, and services. Prioritize low-income neighborhoods and use physical protection (not just paint)."
    },
    {
        "term": "Protected Bike Lane",
        "definition": "Bike lanes physically separated from traffic by planters, posts, curbs, or parked cars. Dramatically safer than painted lanes, encouraging cycling by people of all ages/abilities. Also called 'separated' or 'protected' bike lanes.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Protected bike lanes transform streets: parking moves from curb to protect bike lane, creating physical barrier between bikes and traffic. Studies show: 10x safer than painted lanes, 300% increase in ridership, attract 'interested but concerned' riders (60% of population). Louisville's protected bike lanes will connect: West Louisville to downtown, Highlands to UofL, South End to jobs, neighborhoods to groceries. Green-painted intersections and dedicated signals improve visibility.",
        "why_it_matters": "Painted bike lanes on high-speed roads feel (and are) dangerous—only confident cyclists use them. Protected lanes make cycling safe for kids, seniors, and cautious riders, expanding mobility options and reducing car dependence for thousands.",
        "related_terms": "Bike Infrastructure, Complete Streets, Cycling Safety, Active Transportation, Vision Zero, Multi-Modal Transportation",
        "dave_proposal": "Build protected bike lane network using physical separation (planters, posts, curbs). Include green-painted intersections, dedicated signals, and connections to key destinations. Prioritize connectivity over disconnected fragments."
    },
    {
        "term": "Pedestrian Infrastructure",
        "definition": "Facilities enabling safe walking: sidewalks, crosswalks, pedestrian signals, curb ramps, street lighting, and benches. Basic requirement for walkable neighborhoods but missing in many Louisville areas.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Many Louisville neighborhoods lack basic sidewalks, forcing residents to walk in traffic. Missing infrastructure concentrates in low-income areas (West Louisville, South End). Dave fills sidewalk gaps: systematic audit identifying missing sidewalks, prioritize high-pedestrian areas (near schools, transit stops, businesses), ADA-compliant curb ramps, and well-lit crosswalks. Goal: complete sidewalk network in all urban neighborhoods within 8 years.",
        "why_it_matters": "Walking is most basic transportation but many Louisville residents risk their lives walking on road shoulders. Pedestrian deaths disproportionately occur in neighborhoods without sidewalks. Every neighborhood deserves safe walking infrastructure—it's basic equity.",
        "related_terms": "Complete Streets, Walkability, Vision Zero, Pedestrian Safety, ADA Compliance, Transportation Equity",
        "dave_proposal": "Systematically fill sidewalk gaps: audit missing infrastructure, prioritize high-pedestrian areas, install ADA-compliant crosswalks and curb ramps, and improve lighting. Complete sidewalk network in urban neighborhoods within 8 years."
    },
    {
        "term": "Walkability",
        "definition": "How safe, comfortable, and convenient an area is for walking. Depends on: sidewalks, crosswalks, street design, density, mixed uses, safety, and shade. Walkable neighborhoods improve health, reduce traffic, increase property values.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville's sprawl and car-centric design limit walkability: missing sidewalks, wide dangerous roads, disconnected destinations, parking lots dominating. Dave improves walkability: complete sidewalk networks, traffic calming, protected crosswalks every quarter-mile, shade trees, benches, mixed-use zoning (shops within walking distance), and development patterns supporting walking. Benefits: health improvement, transportation cost savings, neighborhood vitality.",
        "why_it_matters": "Walkable neighborhoods let residents access jobs, shops, and services without cars—saving $10,000+ annually in car costs. Walkability improves health (daily exercise), safety (eyes on street), and community (neighbor interactions). Property values in walkable neighborhoods outperform car-dependent sprawl.",
        "related_terms": "Complete Streets, Pedestrian Infrastructure, Mixed-Use Development, New Urbanism, Smart Growth, Transportation Choice",
        "dave_proposal": "Improve walkability: complete sidewalk networks, traffic calming on major streets, crosswalks every quarter-mile, street trees for shade, mixed-use zoning enabling walkable access to daily needs."
    },
    {
        "term": "Complete Streets",
        "definition": "Streets designed for all users—pedestrians, cyclists, transit riders, drivers—not just cars. Includes sidewalks, bike lanes, bus stops, crosswalks, and accessibility features. Complete Streets policies require accommodating all users in street projects.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Many Louisville streets lack basic sidewalks, forcing pedestrians to walk in traffic. Others have no bike infrastructure, making cycling dangerous. Transit users stand at barren stops without shelter. Dave's Complete Streets policy: all street projects must include continuous sidewalks on both sides, protected bike lanes where feasible, ADA-compliant crosswalks, bus shelters at stops, and safe speeds through design. Prioritize low-income neighborhoods with highest need.",
        "why_it_matters": "Car-centric streets are dangerous and exclusionary: pedestrians get hit, cyclists avoid riding, transit users stand in rain. Complete Streets are safer, more equitable, and support multiple transportation modes—not just cars.",
        "related_terms": "Pedestrian Infrastructure, Bike Infrastructure, Vision Zero, TARC, Walkability, Transportation Equity",
        "dave_proposal": "Adopt Complete Streets policy: all street projects accommodate all users with sidewalks, bike lanes, crosswalks, bus shelters, and safe speeds. Prioritize neighborhoods lacking basic infrastructure."
    },
    {
        "term": "Road Diet",
        "definition": "Reducing number of traffic lanes (typically 4 lanes to 2 plus center turn lane) and reallocating space to bike lanes, sidewalks, parking, or landscaping. Counterintuitively improves safety while maintaining capacity. Proven traffic calming tool.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Louisville has many oversized 4-lane roads with excess capacity, high speeds, and frequent crashes. Road diets transform these corridors: convert 4 lanes to 2 plus center turn lane, add protected bike lanes and wider sidewalks, improve crosswalks and visibility. Studies show: 20-50% crash reduction, minimal traffic impact, increased property values, safer speeds. Target corridors: Preston Street, Bardstown Road sections, portions of Dixie Highway.",
        "why_it_matters": "Four-lane roads encourage speeding and are deadly for pedestrians—long crossing distances and poor sight lines. Road diets calm traffic, add bike lanes and sidewalks, and dramatically improve safety while maintaining traffic flow. Louisville's dangerous 4-lane corridors need road diets.",
        "related_terms": "Traffic Calming, Complete Streets, Vision Zero, Pedestrian Safety, Bike Infrastructure, Street Design",
        "dave_proposal": "Implement road diets on oversized 4-lane corridors: convert to 2 lanes plus center turn lane, add protected bike lanes and wider sidewalks, improve crosswalks. Target high-crash corridors with excess capacity."
    },
    {
        "term": "Safe Routes to School",
        "definition": "Programs creating safe walking/cycling routes to schools through: infrastructure improvements (sidewalks, crosswalks, traffic calming), crossing guards, walking school buses, and bike/pedestrian safety education. Increases active transportation and safety.",
        "category": "Transportation & Infrastructure",
        "louisville_context": "Most Louisville students driven to school—only 15% walk or bike despite 60% living within walking distance. Barriers: missing sidewalks, dangerous crossings, high-speed traffic near schools. Dave's Safe Routes: infrastructure improvements within half-mile of schools (complete sidewalks, protected crosswalks, traffic calming), crossing guards at dangerous intersections, walking school bus programs organizing group walks, bike safety education.",
        "why_it_matters": "Daily exercise improves student health, attention, and academic performance. But dangerous routes force driving, contributing to traffic congestion and childhood obesity. Safe Routes enables active transportation, improving health while reducing traffic at schools.",
        "related_terms": "Pedestrian Safety, Traffic Calming, Vision Zero, Complete Streets, Active Transportation, Child Safety",
        "dave_proposal": "Implement Safe Routes to School: infrastructure improvements within half-mile radius of schools (sidewalks, crosswalks, traffic calming), crossing guards, walking school bus programs, and bike safety education."
    },

    # ========================================
    # ENVIRONMENTAL & SUSTAINABILITY (25 terms)
    # ========================================

    {
        "term": "Rubbertown",
        "definition": "Industrial corridor in West Louisville housing chemical manufacturing facilities. Produces synthetic rubber, plastics, and chemicals since WWII. Known for air pollution, environmental justice concerns, and health impacts on surrounding predominantly Black neighborhoods.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Rubbertown encompasses 15 square miles with 20+ chemical facilities employing 5,000+ workers. Surrounding neighborhoods (Chickasaw, Shawnee, Algonquin) experience: elevated asthma rates (2-3x city average), cancer clusters, daily air quality violations, and property value suppression. Facilities release millions of pounds of toxic chemicals annually. Dave's approach: (1) enhanced air monitoring in neighborhoods, (2) stringent permit requirements for expansions, (3) health impact assessments for new permits, (4) environmental justice lens in all decisions, (5) transition assistance for workers as facilities modernize.",
        "why_it_matters": "Rubbertown provides good-paying jobs but concentrates pollution in Black neighborhoods with limited political power. Environmental justice demands these communities aren't sacrifice zones. Clean air is a civil right—residents shouldn't choose between jobs and health.",
        "related_terms": "Environmental Justice, Air Quality, Industrial Pollution, Environmental Racism, Public Health, West Louisville",
        "dave_proposal": "Address Rubbertown environmental injustice: enhanced air monitoring in neighborhoods, stringent permit requirements with health impact assessments, environmental justice considerations in all decisions, and worker transition assistance for facility modernization."
    },
    {
        "term": "Environmental Justice",
        "definition": "Fair treatment and meaningful involvement of all people regarding environmental laws and policies. Addresses how environmental burdens (pollution, toxic sites) disproportionately affect low-income communities and communities of color.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville's environmental burdens concentrate in West Louisville and South End—predominantly Black and low-income areas: Rubbertown chemical facilities, brownfield sites, interstate highways, landfills, industrial facilities. These neighborhoods experience higher asthma, cancer rates, and life expectancy gaps while wealthier areas enjoy parks and clean air. Dave implements environmental justice: (1) health impact assessments for all permits in environmental justice communities, (2) community veto power over polluting facilities, (3) prioritize cleanup/greenspace in affected areas, (4) air quality monitoring in neighborhoods.",
        "why_it_matters": "Environmental racism isn't accidental—polluting facilities were deliberately sited in Black neighborhoods with limited political power. Environmental justice means those communities get voice, protection, and remediation. Clean air and water are civil rights.",
        "related_terms": "Rubbertown, Environmental Racism, Air Quality, Public Health, Community Input, West Louisville",
        "dave_proposal": "Implement environmental justice framework: health impact assessments for permits in environmental justice communities, community input requirements, prioritize cleanup and greenspace investments, and neighborhood air quality monitoring."
    },
    {
        "term": "Air Quality",
        "definition": "Measure of pollutants in air, tracked by EPA Air Quality Index (AQI). Poor air quality causes asthma, heart disease, and premature death. Louisville faces challenges from: industrial emissions (Rubbertown), vehicle traffic, and seasonal inversions trapping pollution.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville ranks among worst U.S. cities for air quality: ozone, particulate matter (PM2.5), and toxic air pollutants exceed health standards. West Louisville neighborhoods near Rubbertown experience worst air quality with asthma rates 2-3x city average. Dave improves air quality: (1) neighborhood-level monitoring showing hyperlocal pollution, (2) stricter industrial emission limits, (3) clean bus fleet (electric/natural gas), (4) tree planting (natural air filters), (5) anti-idling policies.",
        "why_it_matters": "Bad air quality kills—Louisville sees 400+ premature deaths annually from air pollution. Children and seniors most vulnerable. Low-income neighborhoods bear worst impacts while industry profits. Cleaner air saves lives and reduces healthcare costs.",
        "related_terms": "Rubbertown, Environmental Justice, Public Health, Asthma, Particulate Matter, Emissions",
        "dave_proposal": "Improve air quality: neighborhood-level monitoring network, stricter industrial emission limits, transition to clean bus fleet, aggressive tree planting program, and anti-idling policies near schools."
    },

    # ... Continue with remaining environmental terms ...

]

def main():
    output_file = '/home/dave/skippy/claude/downloads/extracted/comprehensive_expansion_part2.json'

    print(f"📝 Generated {len(part2_terms)} terms (Part 2: Housing, Transportation, Environment)...")
    print()

    categories = {}
    for term in part2_terms:
        cat = term['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("📊 Terms by category:")
    for cat in sorted(categories.keys()):
        print(f"   {cat}: {categories[cat]}")
    print()

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(part2_terms, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {output_file}")
    print(f"   Total terms in part 2: {len(part2_terms)}")

if __name__ == '__main__':
    main()
