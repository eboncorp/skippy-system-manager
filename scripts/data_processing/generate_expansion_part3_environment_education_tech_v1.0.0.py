#!/usr/bin/env python3
"""
Generate Part 3 of comprehensive glossary expansion
Categories: Environmental & Sustainability (22), Education (19), Technology & Innovation (13)
Total: 54 new terms
"""

import json

# Part 3: Environmental & Sustainability (22), Education (19), Technology & Innovation (13)
new_terms = [
    # === ENVIRONMENTAL & SUSTAINABILITY (22 terms) ===
    {
        "term": "Metropolitan Sewer District (MSD)",
        "definition": "A special-purpose government agency that provides wastewater treatment and stormwater management for Louisville Metro and surrounding areas, serving approximately 860,000 people across 24 treatment facilities. MSD operates independently from Louisville Metro Government with its own elected board and budget funded through sewer fees, not property taxes. The agency manages over 3,000 miles of sanitary sewers and is under federal consent decree to reduce combined sewer overflows.",
        "category": "Environmental & Sustainability",
        "louisville_context": "MSD rates have increased significantly over the past decade to fund court-mandated infrastructure improvements. The average Louisville household pays $50-70/month for sewer services. MSD's Waterway Protection Tunnel—a massive underground storage system—is being built beneath Louisville to capture overflow during heavy rains, with construction continuing through 2025 at a cost exceeding $1 billion.",
        "why_it_matters": "Your sewer bill is separate from your water bill and property taxes, but MSD's infrastructure investments directly affect your rates. Understanding how MSD works helps you evaluate why sewer rates increase and whether these investments prevent sewage from flowing into the Ohio River during storms.",
        "related_terms": "Combined Sewer Overflow, Louisville Water Company, Stormwater Management, Green Infrastructure, Environmental Compliance",
        "dave_proposal": "Dave will advocate for MSD to accelerate green infrastructure investments (rain gardens, permeable pavement) that reduce overflow at lower cost than tunnels alone. He'll push for MSD to expand its low-income assistance program and increase transparency about rate-setting.",
        "aliases": "MSD, Sewer District, Louisville MSD"
    },
    {
        "term": "Combined Sewer Overflow (CSO)",
        "definition": "A system where stormwater runoff and sewage flow through the same pipes to treatment plants. During heavy rain, these combined systems overflow, releasing untreated sewage and polluted stormwater directly into rivers and streams. Louisville has one of the nation's largest CSO problems with 55 overflow points that discharge approximately 9 billion gallons of untreated sewage and stormwater into the Ohio River annually.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville's CSO system was built 100+ years ago when this design was standard practice. A 2005 federal consent decree requires Louisville to reduce overflows by 98% by 2025. MSD is spending over $1 billion on the Waterway Protection Tunnel and other infrastructure to meet this deadline, with costs passed to ratepayers through sewer bills.",
        "why_it_matters": "CSOs contaminate Louisville's waterways with raw sewage, creating public health risks and environmental damage. The massive infrastructure investments to fix this problem directly impact your monthly sewer bills, which have tripled since 2005 and will continue increasing.",
        "related_terms": "Metropolitan Sewer District, Stormwater Management, Green Infrastructure, Environmental Compliance, Water Quality",
        "dave_proposal": "Dave supports completing CSO elimination on schedule while maximizing green infrastructure solutions that provide community benefits (parks, rain gardens, tree canopy) rather than only underground tunnels. He'll advocate for MSD to pursue federal infrastructure grants to reduce ratepayer burden.",
        "aliases": "CSO, Sewer Overflow, Sewage Overflow"
    },
    {
        "term": "Stormwater Management",
        "definition": "Systems and practices that control rainwater runoff to prevent flooding, reduce pollution, and protect water quality. Traditional stormwater management uses pipes and detention basins; modern approaches include green infrastructure like rain gardens, bioswales, permeable pavement, and urban tree canopy that absorb rainwater where it falls rather than channeling it into sewers and streams.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville's aging combined sewer system creates severe stormwater challenges. MSD has begun investing in green infrastructure—having installed over 250 green stormwater projects since 2009—but still relies heavily on expensive underground storage. Development regulations now require new construction to manage stormwater on-site, reducing burden on public systems.",
        "why_it_matters": "Poor stormwater management causes basement flooding, street flooding, and sewage overflows that contaminate waterways. The approach Louisville takes—expensive tunnels versus green infrastructure—affects your sewer rates, neighborhood flooding risk, and community benefits like parks and tree canopy.",
        "related_terms": "Combined Sewer Overflow, Metropolitan Sewer District, Green Infrastructure, Flood Prevention, Urban Heat Island",
        "dave_proposal": "Dave will create an Office of Green Infrastructure within Metro Government to coordinate stormwater management across MSD, Public Works, and Parks. His $1.025 billion budget includes funding to expand tree canopy and rain gardens that manage stormwater while cooling neighborhoods and improving quality of life.",
        "aliases": "Stormwater Control, Drainage Management, Runoff Management"
    },
    {
        "term": "Green Infrastructure",
        "definition": "Nature-based systems that manage stormwater, reduce urban heat, improve air quality, and provide community benefits using vegetation, soil, and natural processes. Examples include rain gardens, bioswales, green roofs, urban forests, permeable pavement, and constructed wetlands. Green infrastructure costs 20-30% less than traditional gray infrastructure (pipes and tunnels) while delivering multiple community benefits.",
        "category": "Environmental & Sustainability",
        "louisville_context": "MSD has installed over 250 green stormwater projects since 2009, including rain gardens in Shawnee Park and bioswales in the Portland neighborhood. However, green infrastructure represents less than 5% of Louisville's total CSO investment, with most funding going to underground tunnels. Louisville has significant opportunity to expand green infrastructure in partnership with Parks Department and community organizations.",
        "why_it_matters": "Green infrastructure provides better value than pipes and tunnels by managing stormwater while also reducing flooding, cooling neighborhoods, creating habitat, and improving property values. Communities with green infrastructure see lower sewer rates and higher quality of life than those relying solely on underground systems.",
        "related_terms": "Stormwater Management, Combined Sewer Overflow, Metropolitan Sewer District, Urban Heat Island, Tree Canopy",
        "dave_proposal": "Dave will shift Louisville's infrastructure priorities toward green solutions that deliver multiple benefits. His budget-neutral approach reallocates $15 million annually from planned gray infrastructure to green infrastructure, creating jobs while cooling neighborhoods and managing stormwater more cost-effectively.",
        "aliases": "Natural Infrastructure, Green Stormwater Infrastructure, Nature-Based Solutions"
    },
    {
        "term": "Louisville Water Company",
        "definition": "A publicly-owned utility that provides drinking water to approximately 860,000 people in Louisville Metro and surrounding counties, drawing water from the Ohio River and treating it at two facilities. Unlike MSD (sewers), Louisville Water is governed by appointed commissioners and funded through water rates. The utility is nationally recognized for water quality, operating one of the oldest continuously operating water companies in the US (founded 1860).",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville Water owns the B.E. Payne Water Treatment Plant (world's largest capacity treatment plant when built in 1909) and the newer Crescent Hill facility. The utility supplies water not just to Louisville Metro, but also to parts of Bullitt, Shelby, Spencer, and Oldham counties. Average Louisville household pays $35-45/month for water service.",
        "why_it_matters": "Your water bill is separate from your sewer bill and property taxes. Understanding that Louisville Water is publicly owned (unlike private water companies in some cities) means local control over rates and service quality. The utility's financial health affects your water rates and Louisville's economic development competitiveness.",
        "related_terms": "Metropolitan Sewer District, Public Utilities, Utility Rates, Infrastructure Investment",
        "dave_proposal": "Dave supports continued public ownership of Louisville Water and will advocate for the utility to expand its lead service line replacement program, prioritizing low-income neighborhoods and homes with children. He'll work to ensure water remains affordable through expanded assistance programs.",
        "aliases": "Louisville Water, Water Company, LWC"
    },
    {
        "term": "Urban Heat Island Effect",
        "definition": "The phenomenon where cities are significantly warmer than surrounding rural areas due to dark pavement, rooftops, and lack of vegetation that absorb and retain heat. Urban areas can be 15-20°F hotter than nearby countryside during summer, increasing energy costs, heat-related illness, and air pollution. Low-income neighborhoods with less tree canopy suffer the most severe heat island effects.",
        "category": "Environmental & Sustainability",
        "louisville_context": "West Louisville neighborhoods experience temperatures 10-15°F hotter than East End areas during summer due to less tree canopy, more pavement, and fewer parks. Neighborhoods like Russell, Parkland, and California have tree canopy coverage below 20% compared to 40-50% in wealthier East End neighborhoods. This disparity contributes to higher cooling costs and heat-related health problems in low-income communities.",
        "why_it_matters": "Urban heat islands aren't just uncomfortable—they increase your electricity bills, worsen asthma and heart disease, and can be deadly during heat waves. The unequal distribution of heat burden across Louisville reflects and reinforces racial and economic inequality, with vulnerable populations suffering most.",
        "related_terms": "Tree Canopy, Environmental Justice, Green Infrastructure, Climate Action, Health Equity",
        "dave_proposal": "Dave's Community Wellness Centers will prioritize West Louisville neighborhoods as cooling centers during heat emergencies. His $1.025 billion budget includes expanded Urban Forestry funding to plant 50,000 trees over 4 years, prioritizing heat island neighborhoods. All street reconstruction projects will include increased tree plantings and permeable pavement.",
        "aliases": "Heat Island, Urban Heat, Heat Island Effect"
    },
    {
        "term": "Tree Canopy",
        "definition": "The layer of leaves, branches, and stems of trees that cover the ground when viewed from above, measured as percentage of land area. Urban tree canopy provides multiple benefits: cooling neighborhoods (reducing temperatures 5-15°F), managing stormwater (mature trees absorb 1,000+ gallons annually), improving air quality, increasing property values, and enhancing mental health. Cities target 40%+ canopy coverage for health and environmental benefits.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville's overall tree canopy is approximately 37%, but distribution is highly unequal. East End neighborhoods exceed 50% canopy while West Louisville neighborhoods often have less than 20%. Louisville loses approximately 500 acres of tree canopy annually to development. Metro Government's Urban Forestry budget is approximately $2 million annually—inadequate to reverse canopy loss or address inequality.",
        "why_it_matters": "Tree canopy directly affects your quality of life, property values, cooling costs, and health. Neighborhoods with low tree canopy suffer hotter summers, more flooding, worse air quality, and lower property values. Tree canopy inequality is environmental injustice that perpetuates racial and economic disparities.",
        "related_terms": "Urban Heat Island, Green Infrastructure, Environmental Justice, Stormwater Management, Climate Action",
        "dave_proposal": "Dave will quadruple Louisville's Urban Forestry budget from $2 million to $8 million annually within his $1.025 billion budget, funded by reallocating unnecessary economic development incentives. This funds planting 50,000 trees over 4 years, prioritizing low-canopy neighborhoods, with preference for native species and community engagement in planting locations.",
        "aliases": "Urban Canopy, Forest Canopy, Tree Cover"
    },
    {
        "term": "Climate Action Plan",
        "definition": "A strategic roadmap outlining how a city will reduce greenhouse gas emissions and prepare for climate change impacts like extreme heat, flooding, and severe weather. Effective climate plans include emission reduction targets, adaptation strategies, equity considerations, implementation timelines, and progress metrics. Louisville's 2019 Climate Action Plan set a goal to achieve 100% renewable energy community-wide by 2040.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville released a Climate Action Plan in 2019 but has made limited progress implementing key strategies. The plan identified transportation (36% of emissions), electricity (31%), and buildings (21%) as major emission sources. Implementation has been hampered by lack of dedicated funding and staffing. Louisville has no Chief Sustainability Officer or dedicated Office of Sustainability to drive implementation.",
        "why_it_matters": "Climate change isn't a distant threat—Louisville already experiences more frequent flooding, intense heat waves, and severe storms. Without serious climate action, these impacts will worsen, disproportionately harming low-income communities and costing taxpayers more in emergency response and infrastructure repairs.",
        "related_terms": "Greenhouse Gas Emissions, Renewable Energy, Climate Adaptation, Environmental Justice, Sustainability Office",
        "dave_proposal": "Dave will create an Office of Sustainability within the Mayor's Office, staffed by a Chief Sustainability Officer and 5-person team (funded within $1.025 billion budget) to implement the Climate Action Plan. He'll accelerate renewable energy adoption for Metro buildings, expand TARC service to reduce transportation emissions, and prioritize climate adaptation investments in vulnerable neighborhoods.",
        "aliases": "Climate Plan, Sustainability Plan, Climate Strategy"
    },
    {
        "term": "Greenhouse Gas Emissions",
        "definition": "Gases (primarily carbon dioxide, methane, and nitrous oxide) released by human activities that trap heat in the atmosphere and cause climate change. Major sources include burning fossil fuels for transportation, electricity, and heating; industrial processes; agriculture; and waste decomposition. Cities produce approximately 70% of global greenhouse gas emissions but can reduce emissions through clean energy, efficient buildings, and sustainable transportation.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville emits approximately 13 million metric tons of CO2 equivalent annually. Transportation accounts for 36%, electricity 31%, and buildings 21%. Per capita emissions are higher than national average due to Kentucky's coal-heavy electricity grid and Louisville's sprawling development pattern. LG&E's coal-fired power plants are the region's largest single emission source.",
        "why_it_matters": "Louisville's greenhouse gas emissions contribute to global climate change that already affects our community through increased flooding, extreme heat, and severe weather. Reducing emissions saves money through energy efficiency, improves air quality and health, and creates clean energy jobs while addressing the climate crisis.",
        "related_terms": "Climate Action Plan, Renewable Energy, Energy Efficiency, Air Quality, Climate Change",
        "dave_proposal": "Dave will reduce Metro Government's emissions 50% by 2030 through building efficiency retrofits, renewable energy procurement, and fleet electrification—all funded within the $1.025 billion budget. He'll advocate for LG&E to accelerate coal plant retirements and renewable energy development, and expand TARC service to reduce transportation emissions.",
        "aliases": "Carbon Emissions, GHG Emissions, Climate Pollution"
    },
    {
        "term": "Renewable Energy",
        "definition": "Energy generated from naturally replenishing sources like solar, wind, hydroelectric, and geothermal that don't deplete over time and produce little or no greenhouse gas emissions. Unlike fossil fuels (coal, oil, natural gas), renewable energy is increasingly cost-competitive and becoming cheaper annually. Solar and wind are now the cheapest forms of new electricity generation in most of the United States.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Kentucky's electricity comes primarily from coal (73%) and natural gas (21%), with renewables under 5%. LG&E has begun retiring coal plants but has been slow to develop renewable generation compared to neighboring states. Louisville Metro Government has installed solar panels on several facilities but purchases most electricity from LG&E's fossil fuel-heavy grid. The Falls of the Ohio provides some hydroelectric power.",
        "why_it_matters": "Renewable energy reduces greenhouse gas emissions, improves air quality, stabilizes electricity costs (sunlight and wind are free), and creates local jobs that can't be outsourced. As renewable costs continue falling, communities that transition sooner will save money and attract businesses committed to sustainability.",
        "related_terms": "Climate Action Plan, Greenhouse Gas Emissions, Energy Efficiency, LG&E, Solar Energy",
        "dave_proposal": "Dave will commit Metro Government to 100% renewable electricity by 2030 through solar installations and renewable energy procurement. His budget includes $5 million for solar panels on Metro buildings, starting with community centers and fire stations in low-income neighborhoods, creating local jobs while reducing long-term energy costs within the $1.025 billion budget.",
        "aliases": "Clean Energy, Green Energy, Renewable Power"
    },
    {
        "term": "Energy Efficiency",
        "definition": "Using less energy to perform the same task or produce the same result, typically through better technology, insulation, or practices. Energy efficiency is the cheapest way to reduce energy costs and emissions—every dollar invested in efficiency saves $2-4 in energy costs. Examples include LED lighting (75% less energy than incandescent), building insulation, efficient heating/cooling systems, and weatherization.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville Metro Government spends approximately $15 million annually on electricity and natural gas for 300+ buildings. Most Metro facilities use outdated lighting, inefficient HVAC systems, and poor insulation. Energy efficiency upgrades could reduce energy costs 30-40% ($4.5-6 million annually) while creating local construction jobs. Residential efficiency programs exist through LG&E but serve limited households.",
        "why_it_matters": "Energy efficiency is win-win-win: it saves taxpayer money, reduces greenhouse gas emissions, and creates local jobs. Every dollar Louisville spends on energy efficiency returns multiple dollars in energy savings, allowing resources to shift to other priorities while reducing climate impact.",
        "related_terms": "Renewable Energy, Climate Action Plan, Greenhouse Gas Emissions, Budget Savings",
        "dave_proposal": "Dave will launch a $10 million Metro Building Energy Efficiency Program (funded within $1.025 billion budget) to retrofit government facilities over 4 years, prioritizing projects with fastest payback. Annual energy savings ($4-6 million) will fund program expansion. He'll expand LG&E's residential efficiency programs, prioritizing low-income households to reduce energy burden.",
        "aliases": "Energy Conservation, Efficiency Improvements, Energy Savings"
    },
    {
        "term": "Environmental Justice",
        "definition": "The principle that all people, regardless of race or income, deserve equal protection from environmental hazards and equal access to environmental benefits like clean air, clean water, parks, and tree canopy. Environmental injustice occurs when pollution, industrial facilities, and environmental hazards are concentrated in low-income communities and communities of color while environmental amenities are concentrated in wealthier, whiter areas.",
        "category": "Environmental & Sustainability",
        "louisville_context": "West Louisville neighborhoods face severe environmental injustice: Rubbertown's industrial pollution in predominantly Black neighborhoods, lower tree canopy causing extreme heat, more combined sewer overflows, proximity to highways and truck routes increasing air pollution, and fewer parks. Meanwhile, East End neighborhoods enjoy extensive tree canopy, parks, clean air, and distance from industrial pollution.",
        "why_it_matters": "Environmental injustice isn't accidental—it results from decades of deliberate policy decisions that segregated Louisville and concentrated hazards in Black neighborhoods. This causes real health harm: higher asthma rates, heat-related illness, cancer, and heart disease in affected communities. Addressing environmental injustice is a moral imperative and public health necessity.",
        "related_terms": "Health Equity, Rubbertown, Tree Canopy, Urban Heat Island, Air Quality, Systemic Racism",
        "dave_proposal": "Dave will create an Environmental Justice Office within Metro Government (funded within $1.025 billion budget) to coordinate across departments ensuring equitable distribution of environmental benefits and remediation of environmental harms. All infrastructure investments will be evaluated for environmental justice impact, prioritizing tree planting, green infrastructure, and pollution reduction in overburdened neighborhoods.",
        "aliases": "Environmental Equity, Eco-Justice, Climate Justice"
    },
    {
        "term": "Air Quality Monitoring",
        "definition": "Measuring concentrations of air pollutants like particulate matter (PM2.5), ozone, nitrogen dioxide, and volatile organic compounds to assess health risks and enforce air quality standards. The EPA sets National Ambient Air Quality Standards that cities must meet to protect public health. Real-time monitoring helps identify pollution sources, track trends, and warn residents during poor air quality episodes.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville has approximately 10 permanent air quality monitoring stations operated by LMAPCD (Louisville Metro Air Pollution Control District). However, monitoring is sparse in West Louisville neighborhoods near Rubbertown and industrial areas where pollution is highest. Community groups have deployed low-cost sensors showing significantly worse air quality in fence-line communities than official monitors indicate.",
        "why_it_matters": "You can't address what you don't measure. Inadequate air quality monitoring, especially in pollution-burdened neighborhoods, allows harmful pollution to continue undetected. Better monitoring helps identify pollution sources, hold polluters accountable, and warn vulnerable residents (children, elderly, people with asthma) to stay indoors during poor air quality days.",
        "related_terms": "Rubbertown, Environmental Justice, Air Pollution Control District, Health Equity, Public Health",
        "dave_proposal": "Dave will expand Louisville's air quality monitoring network, installing 20 additional monitors in West Louisville neighborhoods near Rubbertown and industrial areas within his $1.025 billion budget. He'll make real-time air quality data publicly accessible through a mobile app and website, and establish community air quality alert systems for vulnerable neighborhoods.",
        "aliases": "Air Quality Measurement, Pollution Monitoring, Air Monitoring"
    },
    {
        "term": "Rubbertown",
        "definition": "An industrial district in West Louisville containing approximately 20 chemical manufacturing plants and refineries that produce synthetic rubber, plastics, and chemicals. The area is one of the largest synthetic rubber production centers in North America. Rubbertown is immediately adjacent to predominantly Black neighborhoods (Chickasaw, Parkland, Algonquin, Shawnee) that experience elevated pollution exposure and health impacts.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Rubbertown facilities emit hundreds of tons of air pollutants annually including carcinogens like benzene, 1,3-butadiene, and formaldehyde. Neighborhoods near Rubbertown have asthma rates double the Metro average and elevated cancer risks. The Louisville Metro Air Pollution Control District regulates these facilities but has limited enforcement capacity. Multiple chemical leaks, fires, and emission incidents occur annually.",
        "why_it_matters": "Rubbertown exemplifies environmental racism: the deliberate siting of polluting industries in Black neighborhoods that had no political power to resist. Residents didn't choose to live near these hazards—redlining and segregation concentrated Black families here, then industry followed. The resulting health toll (asthma, cancer, respiratory disease) is a preventable injustice.",
        "related_terms": "Environmental Justice, Air Quality Monitoring, Air Pollution Control District, Health Equity, Systemic Racism",
        "dave_proposal": "Dave will strengthen the Air Pollution Control District's enforcement capacity, increase penalties for violations, and require real-time emission monitoring at all Rubbertown facilities with data publicly accessible. His Community Wellness Centers will prioritize Rubbertown fence-line neighborhoods, providing health screening, asthma management, and environmental health education funded within the $1.025 billion budget.",
        "aliases": "Rubbertown Industrial District, Chemical Valley"
    },
    {
        "term": "Air Pollution Control District (APCD)",
        "definition": "The local government agency responsible for monitoring air quality and enforcing air pollution regulations within Louisville Metro. APCD issues permits to industrial facilities, investigates odor and pollution complaints, monitors air quality, and enforces federal Clean Air Act requirements. The agency has authority to levy fines against polluters and require emission reductions.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville Metro Air Pollution Control District operates with a budget of approximately $3.5 million annually and 30 staff members. The agency regulates approximately 700 facilities including Rubbertown chemical plants, LG&E power plants, and smaller industrial sources. APCD has been criticized for inadequate enforcement, slow response to community complaints, and industry-friendly policies that prioritize business concerns over community health.",
        "why_it_matters": "APCD is the frontline defense protecting Louisville residents from air pollution. However, underfunding and lack of political will limit the agency's effectiveness. When APCD doesn't aggressively enforce pollution rules, communities—especially those near Rubbertown and industrial areas—suffer preventable health harm.",
        "related_terms": "Rubbertown, Air Quality Monitoring, Environmental Justice, Public Health, Enforcement",
        "dave_proposal": "Dave will increase APCD's budget by $1 million annually (within $1.025 billion Metro budget) to hire additional inspectors and enforcement staff. He'll direct APCD to prioritize community complaints, increase unannounced facility inspections, and publish enforcement actions transparently. Pollution fines will increase substantially with repeat violators facing facility shutdowns.",
        "aliases": "APCD, Louisville APCD, LMAPCD, Air District"
    },
    {
        "term": "Flood Prevention",
        "definition": "Infrastructure and planning strategies that reduce flooding risk to protect lives, property, and public safety. Approaches include stormwater management systems, flood control structures (levees, floodwalls, detention basins), floodplain regulations that prevent development in flood-prone areas, and green infrastructure that absorbs stormwater. Flood prevention is cheaper than flood recovery—every $1 invested in prevention saves $6 in disaster costs.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville experiences flooding from multiple sources: Ohio River floods (most recent major flood 1997), flash flooding from intense rainstorms (increasingly common with climate change), and basement flooding from combined sewer backups. Shawnee neighborhood faces frequent flooding due to low elevation and inadequate stormwater infrastructure. MSD's CSO improvements will reduce some flooding, but climate change is increasing rainfall intensity.",
        "why_it_matters": "Flooding destroys property, displaces families, and can be deadly. Low-income neighborhoods often face the worst flooding because they lack resources to maintain infrastructure and political power to demand improvements. As climate change increases extreme rainfall, flood prevention investments become more urgent and cost-effective than repeated disaster response.",
        "related_terms": "Stormwater Management, Combined Sewer Overflow, Metropolitan Sewer District, Green Infrastructure, Climate Adaptation",
        "dave_proposal": "Dave will create a comprehensive Flood Prevention Strategy coordinating Metro Public Works, MSD, and Parks to identify high-risk neighborhoods and prioritize green infrastructure investments that manage stormwater while providing community benefits. His $1.025 billion budget includes funding for flood buyouts in repetitive-loss areas, relocating families to safe housing rather than rebuilding in flood zones.",
        "aliases": "Flood Control, Flood Mitigation, Stormwater Control"
    },
    {
        "term": "Sustainability Office",
        "definition": "A dedicated government department that coordinates environmental and sustainability initiatives across all city operations, implements climate action plans, tracks progress toward environmental goals, and ensures sustainability is integrated into all government decisions. Effective sustainability offices have dedicated staff, cabinet-level leadership, and authority to influence budgets and policies across departments.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville has no dedicated Office of Sustainability or Chief Sustainability Officer. Sustainability efforts are scattered across multiple departments with no coordination or accountability. The 2019 Climate Action Plan has no dedicated implementation staff. This lack of institutional capacity means Louisville makes minimal progress on environmental goals while peer cities like Lexington, Indianapolis, and Nashville have sustainability offices driving measurable improvements.",
        "why_it_matters": "Without dedicated staff and leadership, sustainability remains a low priority that loses out to immediate pressures. Peer cities with sustainability offices are reducing emissions, saving energy costs, improving health, and attracting businesses and talent that value environmental leadership. Louisville falls further behind without institutional capacity.",
        "related_terms": "Climate Action Plan, Chief Sustainability Officer, Environmental Justice, Greenhouse Gas Emissions, Organizational Structure",
        "dave_proposal": "Dave will create an Office of Sustainability within the Mayor's Office, led by a cabinet-level Chief Sustainability Officer with a team of 5 staff members (funded within $1.025 billion budget). This office will implement the Climate Action Plan, coordinate environmental justice initiatives, track Metro Government's environmental performance, and ensure sustainability is integrated into all major decisions.",
        "aliases": "Office of Sustainability, Sustainability Department, Environmental Office"
    },
    {
        "term": "Environmental Compliance",
        "definition": "Adherence to federal, state, and local environmental laws and regulations governing air quality, water quality, waste management, stormwater, and pollution. Non-compliance can result in fines, lawsuits, federal enforcement actions, and loss of federal funding. Louisville Metro Government must comply with regulations including Clean Air Act, Clean Water Act, Safe Drinking Water Act, and numerous consent decrees.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville operates under multiple environmental consent decrees including the 2005 CSO consent decree requiring MSD to reduce sewer overflows by 98% by 2025 (cost exceeding $1 billion). Metro Government also faces ongoing EPA scrutiny for air quality, particularly ozone levels that occasionally exceed federal standards. Compliance costs are significant but non-compliance costs are higher through fines and mandatory remediation.",
        "why_it_matters": "Environmental compliance protects public health and avoids costly penalties. However, compliance alone isn't sufficient—meeting minimum requirements often means Louisville continues polluting at levels that harm vulnerable communities. True environmental leadership requires exceeding compliance standards to protect all residents.",
        "related_terms": "Combined Sewer Overflow, Metropolitan Sewer District, Air Pollution Control District, Consent Decree, Federal Regulations",
        "dave_proposal": "Dave will ensure Louisville not only meets compliance requirements but exceeds them to protect public health. He'll accelerate CSO elimination ahead of deadlines, strengthen air quality standards beyond federal minimums, and invest proactively in environmental protection rather than waiting for federal enforcement actions. Compliance will be seen as a floor, not a ceiling.",
        "aliases": "Regulatory Compliance, Environmental Regulations, Compliance Requirements"
    },
    {
        "term": "Water Quality",
        "definition": "The chemical, physical, and biological characteristics of water that determine whether it's safe for drinking, recreation, and supporting aquatic life. Water quality parameters include bacteria levels, dissolved oxygen, pH, temperature, turbidity, and pollutant concentrations. The EPA sets water quality standards that states and localities must meet to protect public health and ecosystems.",
        "category": "Environmental & Sustainability",
        "louisville_context": "The Ohio River provides Louisville's drinking water supply. Louisville Water Company treats river water to meet all federal Safe Drinking Water Act standards. However, the Ohio River receives pollution from upstream cities and CSO discharges from Louisville. Beargrass Creek and other local waterways frequently exceed bacteria standards for recreation due to CSO overflows and stormwater runoff, making them unsafe for swimming or fishing after rain.",
        "why_it_matters": "Water quality affects drinking water safety, recreation opportunities, property values, and ecosystem health. Poor water quality disproportionately impacts low-income communities near polluted waterways and those who can't afford bottled water or water filters. Protecting water quality requires preventing pollution at the source rather than expensive treatment after contamination.",
        "related_terms": "Combined Sewer Overflow, Metropolitan Sewer District, Louisville Water Company, Environmental Compliance, Public Health",
        "dave_proposal": "Dave will accelerate CSO elimination to improve creek and river water quality, making Louisville waterways swimmable and fishable. His Office of Green Infrastructure will prioritize projects that filter stormwater before it reaches creeks. He'll expand Louisville Water Company's lead service line replacement program, prioritizing low-income neighborhoods and homes with children, funded within the $1.025 billion budget.",
        "aliases": "Water Purity, Water Safety, Water Standards"
    },
    {
        "term": "Solid Waste Management",
        "definition": "The collection, transportation, processing, recycling, and disposal of garbage, yard waste, and recyclables. Louisville Metro provides curbside collection of trash, recycling, and yard waste for approximately 180,000 households. Effective waste management reduces pollution, conserves resources through recycling, and protects public health. Louisville's waste goes to landfills in surrounding counties.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville Metro Government operates waste collection services through Metro Public Works with a budget of approximately $35 million annually. The city provides weekly trash and recycling collection and biweekly yard waste collection. Louisville's recycling rate is approximately 25%—below the national average of 32% and far below leading cities achieving 50%+. The city has no municipal composting program despite yard waste comprising 20% of residential waste.",
        "why_it_matters": "Waste management affects your neighborhood cleanliness, property values, and environmental impact. Higher recycling rates reduce landfill costs, conserve resources, and create local jobs. Inadequate waste services disproportionately burden low-income neighborhoods with illegal dumping, litter, and health hazards.",
        "related_terms": "Recycling Program, Environmental Sustainability, Public Works, Waste Reduction",
        "dave_proposal": "Dave will expand Louisville's recycling program to accept more materials (currently limited to basic plastics, paper, glass, metal). He'll launch a municipal composting program allowing residents to compost food scraps and yard waste, reducing landfill costs while creating compost for parks and community gardens. These programs will be funded within the $1.025 billion budget and create local green jobs.",
        "aliases": "Waste Management, Trash Collection, Garbage Service, Sanitation"
    },
    {
        "term": "Recycling Program",
        "definition": "A system that collects, processes, and converts waste materials into new products, conserving natural resources and reducing landfill use. Effective recycling programs require convenient collection, clear communication about what's recyclable, market development for recycled materials, and contamination reduction (keeping non-recyclables out of recycling bins). Recycling creates more jobs per ton than landfilling.",
        "category": "Environmental & Sustainability",
        "louisville_context": "Louisville Metro provides curbside recycling to all residential customers, collecting paper, cardboard, metal cans, glass bottles, and plastics #1-5 and #7. However, contamination rates are high (20-30%) due to confusion about what's recyclable and 'wishcycling' (throwing questionable items in recycling hoping they'll be recycled). Louisville has no curbside composting and limited drop-off recycling for items like electronics and hazardous waste.",
        "why_it_matters": "Recycling reduces waste going to expensive landfills, conserves resources, and creates local processing and manufacturing jobs. However, contamination (putting wrong items in recycling) increases costs and can cause entire loads to be landfilled. Clear communication and convenient recycling options are essential for program success.",
        "related_terms": "Solid Waste Management, Environmental Sustainability, Waste Reduction, Circular Economy",
        "dave_proposal": "Dave will improve Louisville's recycling program through expanded public education about proper recycling, additional drop-off locations for hard-to-recycle items (electronics, batteries, paint), and launching a curbside composting pilot in 5 neighborhoods to test feasibility before citywide expansion. All programs funded within $1.025 billion budget.",
        "aliases": "Curbside Recycling, Waste Recycling, Materials Recovery"
    },
    {
        "term": "Brownfield Redevelopment",
        "definition": "The cleanup and productive reuse of contaminated or potentially contaminated former industrial or commercial properties. Brownfields often sit vacant for decades because liability concerns deter redevelopment. Federal and state programs provide grants and liability protection to encourage cleanup and reuse. Successful brownfield redevelopment removes blight, creates jobs, and prevents sprawl by reusing urban land instead of developing green space.",
        "category": "Economic Development",
        "louisville_context": "Louisville has hundreds of brownfield sites, particularly in West Louisville and along river/railroad corridors where historic industrial activity left contamination. Some notable brownfields include former manufactured gas plant sites, abandoned chemical facilities, and old gas stations. Louisville Forward administers EPA Brownfield Grants but cleanup progresses slowly due to limited funding and complex liability issues.",
        "why_it_matters": "Brownfields create neighborhood blight, reduce property values, pose health risks, and waste valuable urban land that could provide jobs and housing. Brownfield sites cluster in low-income neighborhoods that already face environmental injustice. Prioritizing brownfield cleanup and reuse benefits overburdened communities while preventing sprawl.",
        "related_terms": "Economic Development Incentives, Environmental Justice, Louisville Forward, Environmental Remediation, TIF Districts",
        "dave_proposal": "Dave will make brownfield redevelopment a priority within Louisville Forward, pursuing federal grants aggressively and using TIF financing strategically to fund cleanup. His Office of Environmental Justice (within $1.025 billion budget) will prioritize brownfields in West Louisville, ensuring redevelopment brings community-desired uses (grocery stores, community centers, parks) rather than more industrial facilities.",
        "aliases": "Brownfield Cleanup, Contaminated Site Redevelopment, Environmental Remediation"
    },

    # === EDUCATION (19 terms) ===
    {
        "term": "Jefferson County Public Schools (JCPS)",
        "definition": "The public school district serving Louisville Metro and Jefferson County, operating 173 schools with approximately 100,000 students and 15,000 employees, making it Kentucky's largest and the nation's 28th largest school district. JCPS is governed by an elected 7-member Board of Education, operates independently from Louisville Metro Government, and has a separate budget funded primarily through property taxes and state funding.",
        "category": "Education",
        "louisville_context": "JCPS serves a diverse student population: 38% Black, 38% White, 15% Hispanic, 9% other races. Over 60% of students qualify for free or reduced-price lunch. JCPS has faced persistent challenges with academic achievement gaps, transportation issues, aging facilities, and teacher recruitment. The district's annual budget is approximately $1.5 billion—larger than Louisville Metro Government's budget.",
        "why_it_matters": "JCPS educates the majority of Louisville's children and shapes the city's future workforce. However, Louisville Mayor has no direct authority over JCPS—it's governed by the elected school board. The mayor can influence education through city services (after-school programs, summer jobs, libraries), collaboration with JCPS, and advocacy for state education funding.",
        "related_terms": "School Board, School Funding, Achievement Gap, Superintendent, Education Funding Formula",
        "dave_proposal": "While Dave can't control JCPS operations, he'll expand city-provided educational supports: doubling funding for after-school programs in Metro Parks ($5 million annually), creating summer job programs for 2,000+ high school students, expanding library hours and programming, and ensuring Community Wellness Centers provide homework help and tutoring—all within the $1.025 billion Metro budget.",
        "aliases": "JCPS, Jefferson County Schools, Louisville Public Schools"
    },
    {
        "term": "School Funding Formula",
        "definition": "The complex system determining how much state and local money each school district receives, based on factors like enrollment, student needs (poverty, special education, English learners), and local property wealth. Kentucky's formula is called SEEK (Support Education Excellence in Kentucky). Districts with lower property wealth receive more state aid to equalize funding, while wealthier districts rely more on local property taxes.",
        "category": "Education",
        "louisville_context": "JCPS receives approximately $1.5 billion annually: 50% from state SEEK funding, 40% from local property taxes, 10% from federal sources. Kentucky's education funding has not kept pace with inflation or student needs. JCPS faces a structural funding shortfall of $30-50 million annually, forcing program cuts and deferred maintenance. Louisville's mayor has no direct control over education funding but can advocate for increased state investment.",
        "why_it_matters": "Inadequate education funding directly harms students through larger class sizes, fewer programs, outdated materials, and crumbling facilities. Kentucky ranks in the bottom third nationally for education funding per student. Until the state increases education investment, JCPS will struggle to provide the resources all students deserve.",
        "related_terms": "SEEK Funding, JCPS, Property Tax, State Budget, Education Investment",
        "dave_proposal": "Dave will use his platform to advocate loudly for increased state education funding and oppose any state policies that cut education investment. He'll maximize city support for education within his $1.025 billion budget through expanded after-school programs, summer learning, library services, and partnerships with JCPS to share facilities and reduce costs.",
        "aliases": "Education Funding Formula, SEEK Formula, School Finance"
    },
    {
        "term": "Achievement Gap",
        "definition": "The persistent disparity in academic performance between different groups of students, particularly between white students and students of color, and between economically advantaged and disadvantaged students. Achievement gaps appear in test scores, graduation rates, college enrollment, and other education outcomes. Gaps reflect systemic inequities in resources, opportunities, and support rather than differences in student ability.",
        "category": "Education",
        "louisville_context": "JCPS has significant achievement gaps: Black students graduate at 79% vs. 89% for white students; economically disadvantaged students score 15-20 percentage points lower on state tests than non-disadvantaged students. These gaps reflect decades of segregation, unequal funding, and systemic racism. Schools in West Louisville face higher teacher turnover, less experienced teachers, and larger class sizes than East End schools.",
        "why_it_matters": "Achievement gaps perpetuate racial and economic inequality, limiting opportunities for students of color and low-income students. These gaps aren't inevitable—they result from policy choices about funding, teacher assignment, school boundaries, and resource distribution. Closing gaps requires deliberate action to provide equitable resources and opportunities.",
        "related_terms": "JCPS, Educational Equity, School Funding, Systemic Racism, Opportunity Gap",
        "dave_proposal": "While the mayor doesn't control JCPS, Dave will address factors affecting achievement through city services: Community Wellness Centers providing homework help and tutoring in underserved neighborhoods, summer learning programs preventing summer slide, expanded library programming, and ensuring all neighborhoods have safe routes to school—all within the $1.025 billion budget.",
        "aliases": "Educational Disparities, Test Score Gap, Opportunity Gap"
    },
    {
        "term": "School Board",
        "definition": "The elected governing body that sets policy, hires the superintendent, approves budgets, and provides oversight for a public school district. Kentucky school boards have 5-7 members elected to 4-year terms. School boards are independent from city government—Louisville's mayor has no authority over JCPS Board of Education. Board meetings are open to the public and citizens can provide public comment.",
        "category": "Education",
        "louisville_context": "JCPS Board of Education has 7 members elected from geographic districts across Jefferson County. The board hires and evaluates the JCPS Superintendent, approves the $1.5 billion annual budget, sets academic policies, and makes decisions about school openings/closings and boundaries. Board meetings often feature passionate public testimony about transportation, student assignment, curriculum, and other issues.",
        "why_it_matters": "Your school board members have more direct impact on your children's education than the mayor. School board elections receive less attention than mayor or council races but are crucial for education policy. Voting in school board elections and attending board meetings are how you influence education decisions.",
        "related_terms": "JCPS, Superintendent, School Governance, Education Policy, School Budget",
        "dave_proposal": "Dave can't control the school board but will collaborate closely with JCPS leadership to align city and school district priorities. He'll advocate for board policies that promote equity, support teachers, and close achievement gaps. His Community Wellness Centers will complement school services rather than duplicate them.",
        "aliases": "Board of Education, School Committee, Education Board"
    },
    {
        "term": "Superintendent",
        "definition": "The chief executive officer of a school district, hired by the school board to manage daily operations, implement board policies, prepare budgets, hire staff, and provide educational leadership. The superintendent serves at the pleasure of the board and can be dismissed by board vote. Effective superintendents balance educational expertise, management skills, and political acumen to navigate complex stakeholder demands.",
        "category": "Education",
        "louisville_context": "JCPS Superintendent manages 173 schools, 100,000 students, 15,000 employees, and a $1.5 billion budget—one of the most complex management jobs in the region. JCPS has had significant superintendent turnover, with 6 superintendents since 2010, creating instability and hindering long-term planning. The superintendent works independently from the mayor but can collaborate on shared priorities like student transportation, facility use, and community programs.",
        "why_it_matters": "Superintendent turnover creates instability that harms students and teachers. Frequent changes mean constantly shifting priorities, interrupted initiatives, and leadership vacuums. Supporting superintendent success through reasonable board oversight and community patience is essential for education improvement.",
        "related_terms": "JCPS, School Board, District Leadership, Education Administration",
        "dave_proposal": "Dave will build a collaborative working relationship with the JCPS Superintendent, offering city support for shared goals while respecting the superintendent's independence. He'll coordinate on transportation, facility sharing, after-school programming, and ensuring city services complement rather than compete with school district programs.",
        "aliases": "School Superintendent, District Superintendent, Education Leader"
    },
    {
        "term": "Magnet School",
        "definition": "A public school with specialized curriculum or teaching approach (STEM, arts, Montessori, etc.) designed to attract diverse students from across a district rather than only neighborhood students. Magnet schools were originally created to promote voluntary school integration by offering attractive programs that draw students across racial and economic lines. Admission is typically by lottery when applications exceed capacity.",
        "category": "Education",
        "louisville_context": "JCPS operates numerous magnet programs including Manual's youth performing arts school, duPont Manual's traditional program, Brown School's advanced studies program, and various STEM, Montessori, and language immersion programs. Magnet schools help JCPS maintain some diversity, but transportation challenges and unequal access to program information create equity concerns. Students in East End have better access to magnet programs due to proximity and social capital.",
        "why_it_matters": "Magnet schools can provide excellent educational opportunities and promote diversity. However, if access is unequal, magnets can worsen educational inequality by concentrating resources and motivated families in certain schools while others struggle. Transportation and equitable outreach are essential for magnets to serve their diversity purpose.",
        "related_terms": "JCPS, School Choice, Educational Equity, Student Assignment, Specialty Programs",
        "dave_proposal": "Dave supports JCPS magnet programs but will advocate for the district to ensure equitable access through improved transportation, proactive outreach to all neighborhoods, and lottery systems that prioritize diversity. His Community Wellness Centers will help families navigate school choice options and magnet applications.",
        "aliases": "Magnet Program, Specialty School, Theme School"
    },
    {
        "term": "School Choice",
        "definition": "Policies allowing families to choose which school their children attend rather than being assigned based on home address. School choice includes magnet schools, charter schools, private school vouchers, open enrollment, and student transfer policies. Supporters argue choice increases opportunity and competition; critics argue choice increases segregation and inequality if not carefully designed with equity safeguards.",
        "category": "Education",
        "louisville_context": "JCPS offers school choice through magnet programs and open enrollment allowing transfers to non-neighborhood schools if space is available. Kentucky allows charter schools (though few operate in Louisville) but has no private school voucher program. JCPS's student assignment plan balances choice with diversity goals, though transportation challenges limit real choice for many low-income families without cars.",
        "why_it_matters": "School choice sounds empowering but often benefits families with resources (cars, flexible schedules, knowledge of options) while leaving behind families without those resources. When high-performing students and engaged families leave neighborhood schools, those schools lose resources and political support, creating downward spirals. Equitable choice requires addressing transportation and information barriers.",
        "related_terms": "Magnet School, Charter Schools, Student Assignment, JCPS, Educational Equity",
        "dave_proposal": "Dave supports school choice paired with strong equity safeguards. He'll advocate for JCPS to improve transportation access to magnet schools, ensure all families receive clear information about options, and maintain strong neighborhood schools so choice doesn't create school quality tiers. His Community Wellness Centers will help families understand and navigate school options.",
        "aliases": "Student Choice, Educational Choice, School Selection"
    },
    {
        "term": "Early Childhood Education",
        "definition": "Educational programs for children from birth to age 5, including prekindergarten, Head Start, and childcare programs. High-quality early childhood education provides enormous benefits: improved kindergarten readiness, better long-term academic outcomes, reduced special education needs, and higher lifetime earnings. Every $1 invested in early childhood education returns $7-13 in benefits through improved outcomes and reduced costs.",
        "category": "Education",
        "louisville_context": "Louisville has significant early childhood program gaps. JCPS operates limited prekindergarten programs, mostly serving students with special needs or economic disadvantage. Private childcare is expensive ($8,000-12,000 annually), beyond reach for many families. Federal Head Start serves only 20% of eligible Louisville children due to funding limits. Lack of affordable, quality early childhood education forces parents out of workforce and leaves children unprepared for kindergarten.",
        "why_it_matters": "Early childhood education is the highest-return education investment, but access is severely limited for low-income families. Children entering kindergarten without early education start behind and often never catch up. Meanwhile, expensive childcare forces parents (especially mothers) to leave jobs, harming family finances and workforce participation.",
        "related_terms": "JCPS, Head Start, Childcare, Educational Equity, Workforce Development",
        "dave_proposal": "Dave will expand city-funded early childhood education through Metro Parks community centers, serving 500 additional children annually (funded within $1.025 billion budget). He'll advocate for Kentucky to increase early childhood funding and work with JCPS to expand prekindergarten. Community Wellness Centers will provide early childhood programming, parenting classes, and connections to Head Start and childcare assistance.",
        "aliases": "Pre-K, Prekindergarten, Early Learning, Preschool"
    },
    {
        "term": "After-School Programs",
        "definition": "Supervised activities and enrichment programs for school-age children during the hours between school dismissal and parents' return from work, typically 3-6 PM. Quality after-school programs provide homework help, recreation, arts, sports, and mentoring. After-school programs reduce juvenile crime (which peaks 3-6 PM on school days), improve academic outcomes, and enable parents to work full-time.",
        "category": "Education",
        "louisville_context": "Louisville Metro Parks operates after-school programs at approximately 30 community centers serving about 2,500 children, but waiting lists are common and many neighborhoods lack access. JCPS partners with community organizations on some school-based after-school programs, but funding limits availability. Low-income families need affordable after-school options but often can't access or afford available programs.",
        "why_it_matters": "The hours between 3-6 PM are when juvenile crime peaks and when working parents struggle with childcare. Quality after-school programs keep kids safe, improve academic outcomes, and enable parents to work. However, unequal access means advantaged children gain enrichment while disadvantaged children lack supervision and support.",
        "related_terms": "Youth Programs, Metro Parks, JCPS, Community Centers, Juvenile Crime Prevention",
        "dave_proposal": "Dave will double funding for Metro Parks after-school programs from current $5 million to $10 million annually within his $1.025 billion budget, serving 5,000+ children and eliminating waiting lists. Programs will expand to all community centers and parks, prioritizing underserved neighborhoods. Community Wellness Centers will offer after-school programming including homework help, arts, sports, and mentoring.",
        "aliases": "After-School Care, Youth Programs, Extended Day Programs"
    },
    {
        "term": "Summer Learning Programs",
        "definition": "Educational activities during summer break that prevent 'summer slide'—the learning loss that occurs when students are out of school for 2-3 months. Summer programs combine academics with recreation, arts, and enrichment. Research shows low-income students lose 2-3 months of reading and math skills over summer while middle-class students maintain or gain skills, with summer learning loss accounting for two-thirds of the 9th grade achievement gap.",
        "category": "Education",
        "louisville_context": "JCPS operates limited summer school primarily for credit recovery and students at risk of retention. Metro Parks offers summer day camps that include some educational components but focus mainly on recreation. Private summer programs (camps, enrichment) cost $200-500+ per week, beyond reach for most low-income families. The lack of affordable summer learning options widens achievement gaps.",
        "why_it_matters": "Summer learning loss is a major driver of educational inequality. Advantaged children attend enrichment programs, travel, and experience learning opportunities all summer while disadvantaged children lose academic ground. Two-thirds of the 9th grade achievement gap between low-income and middle-class students results from summer learning loss accumulated over elementary years.",
        "related_terms": "Achievement Gap, Educational Equity, JCPS, Metro Parks, Youth Programs",
        "dave_proposal": "Dave will launch a citywide Summer Learning Initiative providing 6-week programs for 2,000 students annually, combining academics, arts, recreation, and enrichment at no cost to families. The program ($3 million annually within $1.025 billion budget) will operate through Metro Parks community centers and partner with JCPS to align curriculum. Community Wellness Centers will offer summer programming for all ages.",
        "aliases": "Summer School, Summer Enrichment, Summer Programs"
    },
    {
        "term": "School Transportation",
        "definition": "The system that transports students between home and school, including school buses, public transit, walking, and family vehicles. JCPS operates one of the nation's largest and most complex transportation systems, managing over 900 buses traveling 20+ million miles annually to transport 60,000+ students. Student assignment policies prioritizing diversity and school choice make transportation especially challenging and expensive.",
        "category": "Education",
        "louisville_context": "JCPS transportation has faced persistent problems: chronic delays, multi-hour bus rides, driver shortages, and inadequate communication with families. The district spends over $90 million annually on transportation—nearly double the national average per student. Transportation problems disproportionately affect low-income families without cars who can't drive children to school when buses fail. Chronic transportation failures harm attendance and learning.",
        "why_it_matters": "Transportation is the foundation enabling school choice, magnet programs, and diversity. When transportation fails, students miss learning time, families miss work, and trust in JCPS erodes. Families with cars can opt out of school buses, but low-income families depend entirely on district transportation, making failures particularly harmful to vulnerable students.",
        "related_terms": "JCPS, School Choice, Magnet School, Student Assignment, Educational Equity",
        "dave_proposal": "While Dave can't control JCPS transportation, he'll offer city resources to support solutions: Metro EMS providing route planning expertise, Metro Fleet sharing maintenance facilities to reduce JCPS costs, and Traffic Engineering improving traffic flow near schools. He'll advocate for state funding to help JCPS address the driver shortage through competitive wages.",
        "aliases": "School Buses, Student Transportation, School Bus System"
    },
    {
        "term": "School Facilities",
        "definition": "The buildings, playgrounds, athletic fields, and infrastructure where education occurs. Facility quality affects learning—students in well-maintained schools with proper lighting, climate control, and modern equipment perform better than those in deteriorating facilities. Facility investment also signals community priorities and whether all students are valued equally. Deferred maintenance creates safety hazards and accelerating repair costs.",
        "category": "Education",
        "louisville_context": "JCPS faces a massive facilities backlog estimated at $500 million-1 billion in deferred maintenance and needed renovations. Many schools, especially in West Louisville, have aging HVAC systems, leaking roofs, outdated technology infrastructure, and inadequate athletic facilities. Meanwhile, some East End schools have received major renovations or been rebuilt. This facility inequality reflects and reinforces educational inequality.",
        "why_it_matters": "School facilities communicate whether all students are equally valued. When West Louisville students learn in crumbling buildings while East End students enjoy modern facilities, that inequality shapes students' sense of worth and community investment. Facility inequality also creates learning barriers—poor climate control, inadequate technology, and unsafe conditions directly harm education.",
        "related_terms": "JCPS, Educational Equity, Capital Improvement, School Funding, Deferred Maintenance",
        "dave_proposal": "The mayor can't control JCPS facility spending but Dave will advocate loudly for equitable facility investment prioritizing schools serving low-income students. He'll explore city-school partnerships to share facilities (community centers co-located with schools) and coordinate capital improvement projects to reduce costs. Community Wellness Centers may partner with nearby schools to provide shared spaces.",
        "aliases": "School Buildings, School Infrastructure, Educational Facilities"
    },
    {
        "term": "Teacher Recruitment and Retention",
        "definition": "Strategies to attract qualified teachers to the profession and keep them in the classroom rather than leaving for other careers. Teacher turnover harms students through disrupted relationships and less experienced staff. High-poverty schools face the worst retention challenges, creating harmful cycles where students who most need experienced teachers get new teachers who leave after 1-2 years. Competitive salaries, supportive working conditions, and professional development improve retention.",
        "category": "Education",
        "louisville_context": "JCPS faces teacher shortages and high turnover, particularly in high-poverty schools and hard-to-staff subjects (math, science, special education). Starting JCPS teacher salary is approximately $46,000—below surrounding suburban districts and insufficient for Louisville's cost of living. Teacher turnover rates exceed 20% annually in some high-poverty schools compared to under 10% in affluent schools. Working conditions (large class sizes, lack of planning time, limited resources) drive departures.",
        "why_it_matters": "Students can't learn without qualified, stable teachers. When teachers constantly turn over, students lose continuity and schools lose institutional knowledge. High-poverty schools' inability to retain teachers perpetuates achievement gaps—students who most need experienced, skilled teachers instead get inexperienced teachers on their way out.",
        "related_terms": "JCPS, Achievement Gap, Educational Equity, Teacher Salaries, Working Conditions",
        "dave_proposal": "The mayor can't set JCPS teacher salaries but Dave will advocate for competitive teacher pay and oppose state policies that limit district flexibility. He'll create partnerships providing JCPS teachers with city resources: free recreation center memberships, priority child enrollment in city programs, and housing down payment assistance for teachers living in Louisville (funded within $1.025 billion budget).",
        "aliases": "Teacher Retention, Teacher Staffing, Teacher Turnover"
    },
    {
        "term": "School Resource Officer (SRO)",
        "definition": "A sworn law enforcement officer assigned to work in schools, providing security, building relationships with students, teaching law-related classes, and responding to incidents. SRO programs aim to improve school safety and police-youth relationships. However, SROs' presence can criminalize normal adolescent behavior, with Black students disproportionately arrested for minor infractions. Many districts are reconsidering SRO programs and investing instead in counselors and mental health support.",
        "category": "Education",
        "louisville_context": "JCPS partners with LMPD to provide SROs in high schools and some middle schools, funded through a combination of JCPS and LMPD budgets. SRO presence has been controversial: some families view SROs as essential safety resources while others argue police presence criminalizes students and contributes to school-to-prison pipeline, particularly affecting Black students who are arrested at disproportionate rates for similar behaviors as white students.",
        "why_it_matters": "School safety is essential, but the approach matters enormously. Police in schools can either build positive relationships or criminalize typical adolescent mistakes. Data shows Black students are arrested more often than white students for identical behaviors when SROs are present. Whether SRO funding is the best investment for safety—versus counselors, mental health support, and conflict resolution programs—is a crucial policy question.",
        "related_terms": "JCPS, LMPD, School Safety, School-to-Prison Pipeline, Youth Development",
        "dave_proposal": "Dave will work with JCPS and LMPD to ensure SROs receive extensive youth development and de-escalation training, establish clear policies limiting arrests for minor infractions, and require data collection on SRO interactions by race. He'll advocate for balancing SRO funding with increased investment in school counselors, social workers, and mental health support.",
        "aliases": "SRO, School Police, Campus Police"
    },
    {
        "term": "School-to-Prison Pipeline",
        "definition": "Policies and practices that push students, particularly students of color and students with disabilities, out of schools and into the juvenile and criminal justice systems. Pipeline contributors include zero-tolerance discipline policies, school resource officers arresting students for minor infractions, expulsions and suspensions that lead to dropout, and inadequate support for students with behavioral health needs. Black students are suspended and expelled at rates 3-4 times higher than white students for identical behaviors.",
        "category": "Education",
        "louisville_context": "JCPS has reduced suspensions and expulsions in recent years through reforms to discipline policies, but significant racial disparities persist. Black JCPS students are still 2-3 times more likely to be suspended than white students for similar behaviors. Students who are suspended or expelled are significantly more likely to drop out, become involved in juvenile justice, and eventually be incarcerated—creating a literal pipeline from school to prison.",
        "why_it_matters": "The school-to-prison pipeline destroys lives and perpetuates racial injustice. When schools respond to misbehavior with exclusion and criminalization rather than support and intervention, they abandon students who most need help. Disproportionate discipline of Black students reflects implicit bias and systemic racism that must be disrupted through policy changes and cultural transformation.",
        "related_terms": "JCPS, School Resource Officer, Juvenile Justice, Racial Equity, Restorative Justice",
        "dave_proposal": "While Dave can't control JCPS discipline policies, he'll expand alternatives to juvenile detention through Community Wellness Centers offering counseling, mentoring, and support for at-risk youth. He'll work with JCPS to provide restorative justice programs and mental health services as alternatives to suspension. His approach treats misbehavior as a call for help rather than a crime.",
        "aliases": "Schoolhouse to Jailhouse, Discipline Disparities, Exclusionary Discipline"
    },
    {
        "term": "Education Attainment",
        "definition": "The highest level of education individuals have completed, measured by census and surveys (less than high school, high school diploma, associate degree, bachelor's degree, graduate degree). Education attainment strongly predicts income, employment, health, and civic participation. Cities with higher education attainment levels attract better jobs and enjoy higher incomes. Improving education attainment requires both better K-12 education and expanded access to higher education.",
        "category": "Education",
        "louisville_context": "Louisville Metro's education attainment lags peer cities: 33% of adults hold bachelor's degrees or higher compared to 40%+ in Nashville, Indianapolis, and Charlotte. West Louisville neighborhoods have attainment rates below 15% while East End neighborhoods exceed 60%, reflecting historic segregation and inequality. Low education attainment limits Louisville's ability to attract high-wage employers and contributes to poverty and health disparities.",
        "why_it_matters": "Education attainment affects entire communities, not just individuals. Low education attainment limits the jobs Louisville can attract, reduces tax revenue, increases poverty and crime, and worsens health outcomes. Improving attainment requires long-term investment in education from pre-K through college, with particular focus on historically underserved communities.",
        "related_terms": "JCPS, Achievement Gap, Higher Education, Economic Development, Workforce Development",
        "dave_proposal": "Dave will expand pathways to education through partnerships with Jefferson Community and Technical College offering tuition-free workforce training in high-demand fields, expanded after-school and summer programs improving K-12 outcomes, and college success coaching through Community Wellness Centers helping students navigate financial aid and college applications (all within $1.025 billion budget).",
        "aliases": "Educational Attainment, Education Level, Degree Attainment"
    },
    {
        "term": "Louisville Free Public Library",
        "definition": "A system of 18 branch libraries across Louisville Metro providing free access to books, internet, computers, educational programming, and community spaces. Libraries serve as essential equalizers, providing resources regardless of income. Libraries offer far more than books: job search assistance, literacy programs, early childhood programming, technology access, and meeting spaces. Annual budget is approximately $28 million (2.7% of Metro budget).",
        "category": "Education",
        "louisville_context": "Louisville's library system includes the Main Library downtown and 17 neighborhood branches, though service levels and hours vary significantly. Some branches have limited hours due to staffing and funding constraints. West Louisville neighborhoods are underserved—the Newburg and Shawnee areas lack nearby libraries. Library funding has not kept pace with demand, forcing reduced hours and program cuts. Libraries increasingly serve as de facto social service providers.",
        "why_it_matters": "Libraries provide essential services that narrow the digital divide, support education, enable job searches, and offer community gathering spaces—especially important for residents who lack internet access, computers, or quiet study spaces at home. Underfunding libraries disproportionately harms low-income communities that depend on library resources.",
        "related_terms": "Educational Equity, Digital Divide, Community Services, Literacy Programs, Public Services",
        "dave_proposal": "Dave will increase library funding by $3 million annually within his $1.025 billion budget, expanding hours (particularly evenings and weekends when working families can visit), increasing programming, and planning for new branch libraries in underserved areas. He'll ensure libraries have resources to serve as community anchors, not just book repositories.",
        "aliases": "LFPL, Public Library, Library System, Louisville Libraries"
    },
    {
        "term": "Literacy Programs",
        "definition": "Educational services that teach reading and writing skills to children and adults, ranging from early childhood literacy initiatives to adult basic education and English as a Second Language (ESL) classes. Literacy is foundational to education, employment, health, and civic participation. Communities with higher literacy rates have lower poverty, better health, and stronger economies. Libraries, schools, nonprofits, and government agencies all provide literacy programming.",
        "category": "Education",
        "louisville_context": "Louisville has significant literacy challenges: approximately 20% of adults function at basic or below-basic literacy levels, limiting employment opportunities and contributing to poverty. West Louisville neighborhoods have even lower literacy rates. Louisville Free Public Library operates literacy programs but serves only a fraction of those needing services. Early childhood literacy programs are limited, contributing to students entering kindergarten behind.",
        "why_it_matters": "Literacy affects everything—employment, health, parenting, civic participation. Adults with low literacy struggle to help children with homework, perpetuating intergenerational poverty. Children without early literacy exposure start school behind and often never catch up. Expanding literacy programming is one of the highest-return investments for reducing poverty and improving community well-being.",
        "related_terms": "Louisville Free Public Library, Adult Education, Early Childhood Education, Educational Equity, Workforce Development",
        "dave_proposal": "Dave will expand literacy programs through increased library funding ($3 million annually within $1.025 billion budget), Community Wellness Centers offering adult literacy and ESL classes, and partnerships with JCPS on early childhood literacy outreach. He'll ensure all Metro-funded programs provide clear, accessible communication recognizing residents' varying literacy levels.",
        "aliases": "Reading Programs, Adult Literacy, Family Literacy, ESL Programs"
    },
    {
        "term": "Digital Divide",
        "definition": "The gap between people who have access to modern information technology (computers, smartphones, high-speed internet) and those who don't, often along income, racial, and geographic lines. The divide includes both access (availability and affordability) and digital literacy (skills to use technology effectively). COVID-19 highlighted the digital divide as students without internet access couldn't participate in remote learning.",
        "category": "Technology & Education",
        "louisville_context": "Approximately 30,000 Louisville households (15%) lack home internet access, with rates exceeding 25% in low-income neighborhoods. During COVID-19 remote learning, JCPS distributed thousands of devices and hotspots but thousands of students still lacked reliable connectivity. Public libraries provide internet access but have limited hours and locations. The digital divide limits education, employment, healthcare access, and civic participation.",
        "why_it_matters": "In the 21st century, internet access is as essential as electricity for education, employment, health, and daily life. Lack of access creates compounding disadvantages—students can't complete homework, job seekers can't apply online, patients can't access telehealth, residents can't participate in civic processes. The digital divide perpetuates and widens existing inequalities.",
        "related_terms": "Broadband Access, Educational Equity, Louisville Free Public Library, Homework Gap, Economic Inequality",
        "dave_proposal": "Dave will expand public Wi-Fi through Metro Parks community centers, libraries, and Community Wellness Centers, ensuring every neighborhood has free internet access within walking distance. He'll partner with JCPS to continue device lending programs and work with internet providers to expand affordable home internet options in underserved areas (funded within $1.025 billion budget).",
        "aliases": "Internet Access Gap, Technology Gap, Connectivity Divide"
    },

    # === TECHNOLOGY & INNOVATION (13 terms) ===
    {
        "term": "Broadband Access",
        "definition": "High-speed internet service capable of supporting modern online activities like video conferencing, streaming, remote work, and online education. The FCC defines broadband as minimum 25 Mbps download/3 Mbps upload, though many activities require faster speeds. Broadband is essential infrastructure for economic development, education, healthcare, and civic participation—as fundamental to 21st-century communities as roads and electricity.",
        "category": "Technology & Innovation",
        "louisville_context": "Most Louisville Metro has access to broadband internet from providers like AT&T, Spectrum, and Google Fiber, but availability varies by neighborhood and affordability remains a barrier. Monthly broadband costs $50-100+, unaffordable for many low-income households. Some rural areas of Jefferson County lack high-speed options. Broadband access correlates strongly with income—nearly all affluent households have home internet while less than 50% of very low-income households do.",
        "why_it_matters": "Broadband access is no longer optional—it's essential for education (homework, research), employment (remote work, job applications), healthcare (telemedicine), and civic participation (government services, public meetings). Lack of affordable broadband creates severe disadvantages that compound over time, particularly for children whose education increasingly depends on internet access.",
        "related_terms": "Digital Divide, Fiber Optic Network, Internet Infrastructure, Educational Equity, Economic Development",
        "dave_proposal": "Dave will work to expand broadband affordability through partnerships with providers to offer low-cost plans ($10-20/month) for low-income households, advocate for state and federal broadband funding for underserved areas, and ensure all Metro facilities offer free public Wi-Fi. These initiatives will be coordinated within his $1.025 billion budget with minimal direct costs.",
        "aliases": "High-Speed Internet, Internet Access, Broadband Internet"
    },
    {
        "term": "Smart City",
        "definition": "Using technology, data, and connectivity to improve city services, infrastructure efficiency, and quality of life. Smart city applications include intelligent traffic systems that reduce congestion, sensors that optimize trash collection, data analytics that predict infrastructure maintenance needs, and digital platforms that improve citizen access to government services. Effective smart cities prioritize equity, privacy, and community benefit over technology for its own sake.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville has implemented limited smart city initiatives: traffic signal coordination downtown, LouieStat data dashboard tracking Metro performance, and some sensor-based parking management. However, Louisville lags peer cities in smart city adoption. Barriers include limited IT capacity, fragmented systems, insufficient broadband infrastructure in some areas, and lack of strategic vision for technology-enabled improvement.",
        "why_it_matters": "Smart city technologies can make government more efficient and responsive while improving daily life—less time in traffic, faster emergency response, cleaner streets, easier access to services. However, technology can also increase surveillance, reinforce existing inequalities, and waste money if not implemented thoughtfully. Smart city investments must prioritize equity and community benefit.",
        "related_terms": "Data Analytics, Digital Services, Broadband Access, Innovation, Government Efficiency",
        "dave_proposal": "Dave will create a Smart City Initiative within Metro IT (funded within $1.025 billion budget) to strategically deploy technology for community benefit: intelligent traffic systems reducing commute times, sensor-based pothole detection accelerating street repairs, and data analytics identifying high-need areas for services. All initiatives will be evaluated for equity impact before deployment.",
        "aliases": "Smart Cities, Digital City, Connected City, Urban Technology"
    },
    {
        "term": "Open Data",
        "definition": "Government data made freely available to the public in machine-readable formats that anyone can access, use, and share without restrictions. Open data includes budgets, crime statistics, restaurant inspections, property records, performance metrics, and more. Open data promotes transparency, enables accountability, supports research, empowers civic tech applications, and can drive economic development through data-driven businesses.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro maintains an open data portal (data.louisvilleky.gov) with datasets including crime, property records, 311 service requests, and restaurant inspections. However, many datasets are outdated, incomplete, or difficult to use. Louisville's open data program lacks dedicated staffing and policy requiring timely data publication. Peer cities like Chicago and New York have more comprehensive, user-friendly open data programs.",
        "why_it_matters": "Open data enables citizen oversight of government, supports journalism and research, empowers community organizations to identify needs, and allows developers to create useful applications. When government hoards data or releases it in unusable formats, it limits accountability and wastes the value data could provide to communities.",
        "related_terms": "Transparency, Government Accountability, Civic Tech, Data Analytics, Public Records",
        "dave_proposal": "Dave will strengthen Louisville's open data program by establishing an Open Data Policy requiring all departments to publish key datasets quarterly, hiring a Chief Data Officer to coordinate data publication (within $1.025 billion budget), improving data portal usability, and hosting regular community events where residents can learn to use government data.",
        "aliases": "Public Data, Government Data, Data Transparency"
    },
    {
        "term": "Digital Services",
        "definition": "Government services delivered online rather than requiring in-person visits or phone calls, such as permit applications, bill payment, service requests, benefit applications, and records searches. Well-designed digital services are available 24/7, mobile-friendly, and accessible to people with disabilities. Digital services improve convenience for residents and reduce government costs, but must be paired with in-person options for those without internet access or digital literacy.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro offers some digital services through louisvilleky.gov including online bill payment, 311 service requests, and certain permit applications. However, many services still require in-person visits or phone calls. Metro's website is difficult to navigate and many online forms are poorly designed. Louisville lags peer cities in digital service delivery, forcing unnecessary trips to government offices and long phone wait times.",
        "why_it_matters": "Poor digital services waste residents' time and increase government costs. When you must take time off work to visit Metro Hall for something that could be done online, that's a failure of government service design. Digital services done well increase efficiency and equity, but poorly designed digital services exclude people without internet access or digital skills.",
        "related_terms": "E-Government, Online Services, Customer Service, Digital Divide, Government Efficiency",
        "dave_proposal": "Dave will create a Digital Services Team within Metro IT (5 staff, funded within $1.025 billion budget) dedicated to redesigning government services for online delivery with user-friendly design, mobile compatibility, and accessibility. Priority services include permitting, license renewal, benefit applications, and service requests. All digital services will include clear paths to human assistance for those needing help.",
        "aliases": "Online Services, E-Government, Digital Government, Web Services"
    },
    {
        "term": "Civic Technology (Civic Tech)",
        "definition": "Technology tools and platforms that enable citizen engagement with government, facilitate community organizing, or improve civic life. Examples include apps reporting potholes to city government, platforms connecting volunteers with nonprofits, online tools for participatory budgeting, and websites making government data accessible. Civic tech can strengthen democracy by lowering barriers to participation and increasing government accountability.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville has limited civic tech presence. The city's 311 app (Louisville Metro Call Center) allows service requests but has poor user ratings due to limited functionality. Civic tech organizations like Code for America have not established sustained presence in Louisville. Some local nonprofits use technology for organizing but Louisville lacks the civic tech ecosystem found in cities like Boston, Chicago, or Oakland.",
        "why_it_matters": "Civic tech can make government more responsive and accessible while empowering community organizing. However, technology alone doesn't create participation—it must be paired with genuine government commitment to act on community input. Civic tech can also reinforce inequality if it primarily serves tech-savvy residents while excluding others.",
        "related_terms": "Digital Services, Open Data, Civic Engagement, Technology Innovation, Participatory Budgeting",
        "dave_proposal": "Dave will support civic tech development through partnerships with local universities and tech communities, improved government APIs allowing civic tech apps to access Metro data, and grants for civic tech projects addressing community needs (funded within $1.025 billion budget). He'll ensure civic tech complements rather than replaces in-person engagement options.",
        "aliases": "Civic Tech, Government Technology, Democracy Technology, GovTech"
    },
    {
        "term": "Data Privacy",
        "definition": "Protection of individuals' personal information from unauthorized access, use, or disclosure. Government collects massive amounts of sensitive data (health records, tax information, criminal records, addresses) that must be secured and used only for legitimate purposes with appropriate consent. Data privacy includes both cybersecurity (preventing hacks) and policies limiting how government shares or sells resident data to third parties.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro Government collects extensive resident data through tax collection, police records, health services, 311 requests, and other interactions. Metro has experienced data breaches including a 2018 incident where police body camera footage was improperly accessed. Metro's data privacy policies are scattered across departments with no comprehensive framework. Unlike some cities, Louisville lacks strong policies limiting data sharing with federal immigration enforcement.",
        "why_it_matters": "Government data breaches can expose your social security numbers, health information, addresses, and other sensitive data to identity thieves or other harms. Beyond security, government must have clear policies about what data is collected, how it's used, who it's shared with, and how long it's retained. Weak privacy protections disproportionately harm vulnerable communities including immigrants, domestic violence survivors, and others.",
        "related_terms": "Cybersecurity, Government Accountability, Civil Liberties, Data Protection, Public Records",
        "dave_proposal": "Dave will establish comprehensive Data Privacy and Protection Policy within his first 100 days, including encryption requirements, breach notification procedures, limits on data retention, and strict controls on data sharing (especially with federal immigration enforcement). He'll create a Chief Privacy Officer position within IT (funded within $1.025 billion budget) to enforce privacy protections.",
        "aliases": "Data Protection, Privacy Rights, Information Privacy, Data Security"
    },
    {
        "term": "Cybersecurity",
        "definition": "Protection of computer systems, networks, and data from digital attacks, unauthorized access, and damage. Government cybersecurity must protect resident data (social security numbers, health records, tax information), critical infrastructure (water, power, emergency services), and government operations from ransomware, hackers, and other threats. Cybersecurity requires technology defenses, staff training, incident response planning, and regular security audits.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro IT provides cybersecurity for government systems but faces resource constraints and rapidly evolving threats. Like many cities, Louisville is a ransomware target—hackers who encrypt government data and demand payment to restore access. Metro has not suffered a major ransomware attack but many peer cities have, causing service disruptions costing millions. Metro's cybersecurity staffing and funding are inadequate given the threats.",
        "why_it_matters": "Cyberattacks can shut down government services for weeks, expose your personal data to criminals, and cost millions in recovery and ransom payments. Ransomware attacks have crippled cities' ability to provide basic services including emergency response. Cybersecurity isn't optional—it's essential infrastructure that requires sustained investment.",
        "related_terms": "Data Privacy, Information Technology, Government Operations, Critical Infrastructure, Risk Management",
        "dave_proposal": "Dave will increase Metro IT's cybersecurity capacity by adding 3 cybersecurity specialists (funded within $1.025 billion budget), implementing comprehensive security training for all Metro employees, establishing incident response protocols, and conducting regular security audits. He'll ensure critical systems have offline backups preventing ransomware from crippling government operations.",
        "aliases": "Information Security, IT Security, Digital Security, Network Security"
    },
    {
        "term": "Geographic Information Systems (GIS)",
        "definition": "Technology that captures, stores, analyzes, and displays geographically referenced data—essentially creating maps with layers of information. Government uses GIS for planning (identifying areas needing parks), emergency response (mapping ambulance coverage), infrastructure management (tracking pothole locations), and analysis (understanding service distribution by neighborhood). GIS makes spatial patterns visible, supporting better decision-making.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro Government uses GIS extensively for property assessment, planning, public works, utilities, and emergency services. LOJIC (Louisville/Jefferson County Information Consortium) maintains shared GIS infrastructure across government agencies and utilities. However, GIS capacity varies across departments and many potential applications remain underdeveloped. Public-facing mapping tools are limited compared to peer cities.",
        "why_it_matters": "GIS reveals patterns invisible in spreadsheets—like showing which neighborhoods have the most potholes, least tree canopy, or slowest emergency response times. These spatial patterns often reflect systemic inequities in service delivery. Making GIS data accessible helps communities advocate for equitable services and holds government accountable for geographic disparities.",
        "related_terms": "Data Analytics, Open Data, Urban Planning, Infrastructure Management, Spatial Analysis",
        "dave_proposal": "Dave will expand public access to GIS data through improved online mapping tools showing service distribution (pothole repairs, police response times, tree canopy) by neighborhood. This transparency (within $1.025 billion budget for minor IT costs) will enable residents to identify service inequities and hold government accountable for equitable resource allocation across all Louisville communities.",
        "aliases": "GIS, Mapping Systems, Spatial Data, Geographic Data"
    },
    {
        "term": "311 System",
        "definition": "A non-emergency phone number and digital platform for residents to request city services, report issues, and get information. 311 systems handle potholes, streetlight outages, trash collection problems, abandoned vehicles, code violations, and general questions. Good 311 systems track requests, provide status updates, generate data for service improvements, and integrate with online/mobile reporting. 311 systems free 911 for true emergencies.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville operates 311 service (MetroCall) by phone, online, and mobile app for service requests and general information. The system receives approximately 300,000 contacts annually. However, Louisville's 311 system has significant problems: long wait times, requests that disappear without resolution, no follow-up communication, and poor integration across departments. The mobile app has low ratings due to poor functionality and lack of transparency about request status.",
        "why_it_matters": "311 is your primary way to request city services and report problems. When 311 systems work well, potholes get filled, streetlights get fixed, and you receive updates on request status. When they fail, problems go unaddressed, trust in government erodes, and people flood 911 with non-emergencies. Good 311 data also helps government identify service needs and deploy resources efficiently.",
        "related_terms": "Customer Service, Digital Services, Government Accountability, Service Delivery, Public Works",
        "dave_proposal": "Dave will overhaul Louisville's 311 system within his first 6 months: hiring additional operators to reduce wait times, implementing automated status updates via text/email, integrating 311 fully with department work order systems so requests don't disappear, and redesigning the mobile app for better functionality (all within $1.025 billion budget). He'll publish 311 data showing response times by neighborhood to ensure equitable service.",
        "aliases": "311, MetroCall, Non-Emergency Services, Citizen Services"
    },
    {
        "term": "Technology Procurement",
        "definition": "The process government uses to purchase technology systems, software, and services. Traditional procurement emphasizes lowest bid and rigid specifications written years before purchase, often resulting in expensive systems that don't meet user needs. Modern procurement uses agile methods, modular purchasing, open-source software, and evaluation criteria emphasizing outcomes over features. Poor tech procurement wastes millions on systems that fail or deliver minimal value.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro's technology procurement follows traditional government purchasing processes that prioritize lowest cost and prescriptive requirements. This has led to expensive failures including the payroll/HR system that launched years late and millions over budget. Metro typically purchases large, proprietary systems requiring expensive vendor relationships rather than modular, open-source alternatives. Procurement staff lack technology expertise to evaluate proposals effectively.",
        "why_it_matters": "Government wastes enormous sums on failed technology projects due to outdated procurement practices. When Louisville spends millions on systems that don't work or vendors that lock government into expensive contracts, that's money unavailable for services residents need. Modern procurement methods can deliver better technology at lower cost while avoiding vendor lock-in.",
        "related_terms": "Government Contracting, IT Systems, Budget Management, Open Source Software, Vendor Management",
        "dave_proposal": "Dave will reform Metro's technology procurement by establishing an IT Procurement Modernization Team (within $1.025 billion budget) with both procurement and technology expertise. New policies will prioritize modular purchasing, open-source alternatives, agile development methods, and outcomes-based contracts. He'll end vendor lock-in by requiring data portability and avoiding proprietary systems where open alternatives exist.",
        "aliases": "IT Procurement, Technology Purchasing, Technology Contracting, Software Acquisition"
    },
    {
        "term": "Open Source Software",
        "definition": "Computer software with source code freely available for anyone to inspect, modify, and enhance. Open source software contrasts with proprietary software that only vendors can modify and requires licensing fees. Governments using open source can avoid vendor lock-in, customize software for specific needs, share solutions with other cities, and often reduce costs. Examples include Linux, Firefox, and many government-specific applications developed collaboratively by multiple cities.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville Metro Government relies heavily on proprietary software from vendors like Microsoft, Oracle, and Tyler Technologies, creating expensive long-term contracts and vendor lock-in. Metro has limited adoption of open source alternatives despite successful use by peer cities. The preference for familiar proprietary vendors over open source alternatives costs Louisville millions in licensing fees and limits flexibility to customize systems for local needs.",
        "why_it_matters": "Proprietary software creates dependency on vendors who can raise prices and control your systems. When multiple cities need similar software (permitting, 311, budgeting), collaborating on open source solutions is more cost-effective than each city paying vendors for proprietary systems. Open source also enables transparency—residents can inspect government software for privacy and security concerns.",
        "related_terms": "Technology Procurement, Vendor Lock-In, IT Systems, Cost Savings, Government Technology",
        "dave_proposal": "Dave will establish an 'Open Source First' policy: Metro IT must evaluate open source alternatives before purchasing proprietary software, documenting why proprietary solutions are chosen. He'll join coalitions of cities collaboratively developing open source government software, sharing costs and solutions. This approach (within $1.025 billion budget) will reduce licensing fees while increasing flexibility and transparency.",
        "aliases": "Open Source, Free Software, Open Source Technology, Collaborative Software"
    },
    {
        "term": "LouieStat",
        "definition": "Louisville Metro Government's performance management system that tracks key metrics across departments to improve accountability, identify problems early, and make data-driven decisions. Modeled on CitiStat (pioneered by Baltimore), LouieStat holds regular meetings where department directors review performance data and problem-solve. The system aims to shift government culture from activity-based ('we're busy') to results-based ('we're improving outcomes').",
        "category": "Technology & Innovation",
        "louisville_context": "Mayor Fischer launched LouieStat in 2011 as a transparency and accountability initiative. The program tracks metrics like pothole filling, code enforcement, permitting times, and service response. However, LouieStat has diminished over time with less frequent meetings, limited public reporting, and weak consequences for poor performance. The dashboard (louisvilleky.gov/louiestat) contains outdated data and broken links, limiting transparency value.",
        "why_it_matters": "Performance management systems like LouieStat can drive real improvements if used consistently with leadership commitment and consequences. However, if metrics are gamed, data is ignored, or there's no follow-through on problems identified, performance systems become useless bureaucratic exercises. LouieStat's decline signals weakened accountability in Metro Government.",
        "related_terms": "Performance Management, Government Accountability, Data Analytics, Transparency, Results-Based Management",
        "dave_proposal": "Dave will revitalize LouieStat through monthly performance review meetings with all department directors, public dashboard with current data updated weekly, consequences for persistent poor performance (including leadership changes), and expansion beyond outputs (activities) to outcomes (results). He'll make LouieStat a central accountability tool within his $1.025 billion budget with minimal additional costs.",
        "aliases": "Performance Management, Data Dashboard, Accountability System"
    },
    {
        "term": "Innovation Lab",
        "definition": "A dedicated team within government focused on testing new approaches to persistent problems, using rapid prototyping, user research, and experimentation. Innovation labs help government become more creative and responsive by providing space to try novel solutions without bureaucratic barriers that slow traditional processes. Successful labs identify promising innovations for scaling across government while discontinuing approaches that don't work.",
        "category": "Technology & Innovation",
        "louisville_context": "Louisville has no formal innovation lab or capacity for rapid testing of new approaches. Metro Government typically implements programs at full scale without small-scale testing, making failures expensive and corrections slow. Peer cities like Philadelphia, Boston, and San Francisco have innovation teams that rapidly test solutions, fail fast when things don't work, and scale successes—enabling more effective, efficient government.",
        "why_it_matters": "Government faces complex problems that traditional bureaucratic approaches often can't solve. Innovation labs provide structured ways to test new ideas quickly and cheaply before committing large budgets. This reduces the risk of expensive failures while increasing the likelihood of discovering approaches that significantly improve residents' lives.",
        "related_terms": "Government Innovation, Pilot Programs, Design Thinking, Problem-Solving, Organizational Learning",
        "dave_proposal": "Dave will create a 5-person Metro Innovation Lab (funded within $1.025 billion budget) reporting directly to the Chief of Staff, empowered to work across departments testing new approaches to persistent problems (homelessness, illegal dumping, abandoned properties). The lab will run rapid pilots, rigorously evaluate results, scale successes, and abandon failures—bringing private sector innovation methods to government problem-solving.",
        "aliases": "Innovation Team, Gov Lab, Innovation Office, I-Team"
    }
]

# Output JSON file
output_file = '/home/dave/skippy/claude/downloads/extracted/glossary_expansion_part3_env_edu_tech.json'

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(new_terms, f, indent=2, ensure_ascii=False)

print(f"Generated {len(new_terms)} new terms:")
print(f"  - Environmental & Sustainability: 22 terms")
print(f"  - Education: 19 terms")
print(f"  - Technology & Innovation: 13 terms")
print(f"\nSaved to: {output_file}")
print(f"\nTotal terms in this expansion: {len(new_terms)}")
