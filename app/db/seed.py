from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

GUIDELINES = [
    # === INDEMNIFICATION ===
    ("indemnification", "Indemnification cap must not exceed 25% of total contract value", "high"),
    ("indemnification", "Mutual indemnification is preferred over one-sided indemnification", "medium"),
    ("indemnification", "Indemnification must survive termination for at least 12 months", "medium"),
    ("indemnification", "Indemnification for third-party IP infringement claims must be unlimited in amount", "high"),
    ("indemnification", "Indemnitee must provide prompt notice of any indemnifiable claim", "medium"),
    ("indemnification", "Indemnitor must have sole control over defense of indemnified claims", "medium"),
    ("indemnification", "Indemnitee must reasonably cooperate in the defense of claims", "low"),
    ("indemnification", "Indemnification must cover reasonable attorneys fees and court costs", "high"),
    ("indemnification", "Indemnification obligations must extend to affiliates and subcontractors", "medium"),

    # === LIMITATION OF LIABILITY ===
    ("liability", "Limitation of liability cap must be at least equal to contract value", "high"),
    ("liability", "Neither party shall be liable for consequential damages", "medium"),
    ("liability", "Liability cap must be a specific dollar amount, not uncapped", "high"),
    ("liability", "Unlimited liability must be excluded for death, bodily injury, fraud, and gross negligence", "high"),
    ("liability", "Liability for breach of confidentiality must be excluded from the general liability cap", "high"),
    ("liability", "Liability for indemnification obligations must be excluded from the general cap", "high"),
    ("liability", "Liability for unauthorized use of intellectual property must be uncapped", "high"),
    ("liability", "Liability cap must not apply to payment obligations", "medium"),
    ("liability", "Each party's aggregate liability must be calculated cumulatively across all claims", "medium"),

    # === TERMINATION ===
    ("termination", "Either party may terminate for convenience with 30 days notice", "low"),
    ("termination", "Termination for cause requires 10 day cure period", "medium"),
    ("termination", "Upon termination, surviving obligations must be clearly listed", "low"),
    ("termination", "Either party may terminate immediately for material breach that remains uncured", "high"),
    ("termination", "Either party may terminate immediately if the other becomes insolvent", "high"),
    ("termination", "Termination must not relieve either party of obligations accrued before termination", "medium"),
    ("termination", "Upon termination, each party must return or destroy the other's confidential information", "high"),
    ("termination", "Termination for convenience must not require payment of early termination fees", "medium"),

    # === GOVERNING LAW & DISPUTE RESOLUTION ===
    ("governing_law", "Governing law should be Delaware or New York law", "medium"),
    ("governing_law", "Dispute resolution must include binding arbitration clause", "medium"),
    ("governing_law", "Venue must be in the same state as governing law", "low"),
    ("governing_law", "Arbitration must be conducted in English by a neutral arbitrator under AAA or JAMS rules", "high"),
    ("governing_law", "Exclusive jurisdiction clauses are preferred over non-exclusive jurisdiction", "medium"),
    ("governing_law", "The prevailing party in any dispute must be entitled to recover reasonable attorneys fees", "medium"),
    ("governing_law", "Class action waivers should be included in dispute resolution provisions", "medium"),
    ("governing_law", "Waiver of jury trial should be included where enforceable", "low"),
    ("governing_law", "Dispute resolution must include a multi-step escalation process before litigation", "medium"),
    ("governing_law", "The UN Convention on Contracts for the International Sale of Goods (CISG) must be expressly excluded", "medium"),

    # === CONFIDENTIALITY ===
    ("confidentiality", "Confidentiality obligations must survive for 3 years post-termination", "high"),
    ("confidentiality", "Definition of confidential information must exclude publicly available data", "medium"),
    ("confidentiality", "Receiving party must notify disclosing party of any breach immediately", "medium"),
    ("confidentiality", "Confidential information must be disclosed only on a need-to-know basis", "high"),
    ("confidentiality", "Compelled disclosure of confidential information requires prompt notice to the disclosing party", "medium"),
    ("confidentiality", "Receiving party must implement reasonable security measures to protect confidential information", "high"),
    ("confidentiality", "Confidential information must not be copied except as necessary for performance", "low"),
    ("confidentiality", "Confidentiality obligations must bind the receiving party's employees and contractors", "high"),
    ("confidentiality", "Trade secrets must be protected indefinitely without time limitation", "high"),

    # === PAYMENT TERMS ===
    ("payment", "Payment terms must be net 30 or better", "low"),
    ("payment", "Late payment interest rate must not exceed 1.5% per month", "medium"),
    ("payment", "All invoices must include PO number reference", "low"),
    ("payment", "Payment must be made in the currency specified in the contract", "medium"),
    ("payment", "Volume discounts must be clearly defined with tier thresholds and retrospective or prospective application", "medium"),
    ("payment", "Expense reimbursement must require prior written approval", "medium"),
    ("payment", "Withholding taxes must be grossed up by the paying party", "high"),
    ("payment", "Invoicing disputes must be raised within 30 days of invoice receipt", "medium"),
    ("payment", "Set-off rights must be mutual between both parties", "medium"),
    ("payment", "Payment terms for SOWs must match the master agreement payment terms", "low"),

    # === RENEWAL ===
    ("renewal", "Auto-renewal requires 60 days advance notice of non-renewal", "high"),
    ("renewal", "Price escalation upon renewal must not exceed 5% annually", "medium"),
    ("renewal", "Renewal terms must be expressly agreed in writing", "medium"),
    ("renewal", "Automatic renewal must include a cap on the number of renewal terms", "medium"),
    ("renewal", "Notice of non-renewal must be delivered in writing via confirmed delivery method", "low"),

    # === DATA PROTECTION & PRIVACY ===
    ("data_protection", "Data breach notification must occur within 72 hours of discovery", "high"),
    ("data_protection", "Cross-border data transfers must have Standard Contractual Clauses or equivalent safeguards", "high"),
    ("data_protection", "Data retention period must not exceed 7 years post-termination", "medium"),
    ("data_protection", "Personal data may only be processed for the specific purposes stated in the contract", "high"),
    ("data_protection", "Data processor must maintain a register of all processing activities", "medium"),
    ("data_protection", "Data processor must assist the controller with data subject access requests", "medium"),
    ("data_protection", "Sub-processing of personal data requires prior written authorization", "high"),
    ("data_protection", "Data Protection Impact Assessment (DPIA) must be conducted for high-risk processing", "high"),
    ("data_protection", "Data processor must implement appropriate technical and organizational security measures under Article 32 GDPR", "high"),
    ("data_protection", "Data processing agreement (DPA) must be executed as part of the main contract", "high"),
    ("data_protection", "CCPA compliance requires that service providers not sell or share personal information", "high"),
    ("data_protection", "Data subjects must have the right to erasure under applicable privacy laws", "high"),
    ("data_protection", "Anonymized or aggregated data must not be used to re-identify individuals", "medium"),
    ("data_protection", "Biometric and genetic data require enhanced protection measures", "high"),

    # === INTELLECTUAL PROPERTY ===
    ("intellectual_property", "All custom-developed IP vests exclusively with the customer", "high"),
    ("intellectual_property", "Pre-existing IP licenses must survive termination", "medium"),
    ("intellectual_property", "License grants must specify whether they are exclusive or non-exclusive", "high"),
    ("intellectual_property", "License grants must specify territory, duration, and field of use", "high"),
    ("intellectual_property", "IP licenses must be perpetual unless expressly stated otherwise", "medium"),
    ("intellectual_property", "Sublicensing rights must be expressly granted in writing", "medium"),
    ("intellectual_property", "Improvements to customer IP must be assigned to the customer", "high"),
    ("intellectual_property", "Moral rights must be waived where permissible under applicable law", "medium"),
    ("intellectual_property", "IP warranties must include warranty of non-infringement", "high"),
    ("intellectual_property", "Open source software usage must be disclosed with license obligations", "medium"),
    ("intellectual_property", "Background IP must be clearly identified and listed in a schedule", "medium"),
    ("intellectual_property", "License fees must be separately stated from service fees", "low"),
    ("intellectual_property", "IP escrow for source code must be required for critical software", "high"),
    ("intellectual_property", "Vendor must defend and indemnify against all third-party IP claims", "high"),

    # === INSURANCE ===
    ("insurance", "Commercial general liability minimum $2M per occurrence / $4M aggregate", "high"),
    ("insurance", "Professional liability / errors omissions insurance minimum $2M per claim", "high"),
    ("insurance", "Cyber liability insurance minimum $2M per occurrence including data breach response", "high"),
    ("insurance", "Workers compensation insurance must comply with statutory requirements", "medium"),
    ("insurance", "Additional insured endorsement must name the customer as an additional insured", "high"),
    ("insurance", "Waiver of subrogation must be included in all insurance policies", "high"),
    ("insurance", "Insurance policies must be primary and non-contributory", "medium"),
    ("insurance", "30 days advance written notice of policy cancellation must be provided", "high"),
    ("insurance", "Self-insured retentions must not exceed $100,000 without approval", "medium"),
    ("insurance", "Automobile liability insurance minimum $1M combined single limit", "medium"),
    ("insurance", "Cyber insurance must include coverage for social engineering and funds transfer fraud", "high"),
    ("insurance", "Umbrella / excess liability insurance minimum $5M per occurrence", "medium"),
    ("insurance", "Insurance coverage must be maintained throughout the contract term and for 3 years after", "high"),

    # === FORCE MAJEURE ===
    ("force_majeure", "Force majeure must expressly include pandemics and cyberattacks", "high"),
    ("force_majeure", "Party claiming force majeure must mitigate impacts within 14 days", "medium"),
    ("force_majeure", "Force majeure relief must not exceed 60 consecutive days", "medium"),
    ("force_majeure", "Force majeure must not excuse payment obligations", "high"),
    ("force_majeure", "Notice of force majeure must be given within 48 hours of the triggering event", "high"),
    ("force_majeure", "Force majeure must include supply chain disruptions and material shortages", "medium"),
    ("force_majeure", "Either party must have the right to terminate after extended force majeure", "medium"),
    ("force_majeure", "Force majeure definition must include acts of government and regulatory changes", "medium"),

    # === WARRANTY ===
    ("warranty", "Services warranty must include workmanlike performance standard", "medium"),
    ("warranty", "Warranty of authority must be mutual for both parties", "low"),
    ("warranty", "Products must be free from defects in materials and workmanship for 12 months", "high"),
    ("warranty", "Services must be performed in a timely and professional manner", "medium"),
    ("warranty", "Warranty must cover compliance with all specifications and requirements", "high"),
    ("warranty", "Warranty remedy must allow for re-performance or refund at customer's option", "high"),
    ("warranty", "Warranty disclaimers must not apply to express warranties made in the contract", "medium"),
    ("warranty", "Pass-through warranties from subcontractors must be assigned to the customer", "medium"),
    ("warranty", "Services must comply with all applicable laws and regulations", "high"),
    ("warranty", "Hardware warranties must be manufacturer's standard plus any additional coverage", "medium"),
    ("warranty", "Warranty of non-infringement must be express and unlimited", "high"),
    ("warranty", "Warranty must include compliance with accessibility standards (ADA, WCAG 2.1 AA)", "medium"),

    # === SERVICE LEVEL AGREEMENT (SLA) ===
    ("sla", "Critical system uptime guarantee must be 99.9% or higher", "high"),
    ("sla", "Credits must be automatic, not requiring customer request", "medium"),
    ("sla", "Critical issue response time must be within 1 hour of notification", "high"),
    ("sla", "Critical issue resolution time must be within 4 hours", "high"),
    ("sla", "High priority issue resolution time must be within 8 business hours", "medium"),
    ("sla", "SLA credits must be capped at 100% of monthly recurring fees", "medium"),
    ("sla", "SLA must define escalation matrix with named contacts and backup personnel", "medium"),
    ("sla", "Monthly SLA reporting must be provided with detailed uptime and incident data", "medium"),
    ("sla", "Failure to meet SLA for 3 consecutive months must trigger termination for cause", "high"),
    ("sla", "SLA must include scheduled maintenance windows with 48-hour advance notice", "low"),
    ("sla", "Emergency maintenance must require customer approval before implementation", "medium"),
    ("sla", "Performance credits are not the sole remedy for SLA breaches", "high"),

    # === AUDIT RIGHTS ===
    ("audit", "Customer must have the right to audit vendor's security controls annually", "high"),
    ("audit", "Audit notice period must not exceed 30 days", "medium"),
    ("audit", "Audits must be conducted no more than once per rolling 12-month period unless triggered by breach", "medium"),
    ("audit", "Audit costs must be borne by the customer unless material non-compliance is found", "medium"),
    ("audit", "Vendor must provide SOC 2 Type II report upon request", "high"),
    ("audit", "Audit rights must cover subcontractors and their facilities", "medium"),
    ("audit", "Non-compliance findings must be remediated within 30 days", "high"),
    ("audit", "Audit rights must survive termination for 2 years", "medium"),

    # === ANTI-CORRUPTION & COMPLIANCE ===
    ("anti_corruption", "Both parties must comply with applicable anti-bribery and anti-corruption laws", "high"),
    ("anti_corruption", "Gifts and entertainment to customer employees must not exceed $100 annual value per person", "high"),
    ("anti_corruption", "Neither party may make improper payments to government officials", "high"),
    ("anti_corruption", "Compliance with the US Foreign Corrupt Practices Act (FCPA) and UK Bribery Act is required", "high"),
    ("anti_corruption", "Anti-corruption representations and warranties must survive for 5 years post-termination", "high"),
    ("anti_corruption", "Any violation of anti-corruption laws must be reported to the other party within 24 hours", "high"),
    ("anti_corruption", "Political contributions must not be made in the other party's name without express authorization", "medium"),
    ("anti_corruption", "Conflicts of interest must be disclosed immediately in writing", "high"),

    # === ASSIGNMENT ===
    ("assignment", "Non-consent assignment is prohibited without prior written approval", "medium"),
    ("assignment", "Change of control constitutes assignment triggering consent rights", "medium"),
    ("assignment", "Assignment to an affiliate is permitted if the affiliate is creditworthy", "low"),
    ("assignment", "Consent to assignment must not be unreasonably withheld or delayed", "medium"),
    ("assignment", "The assigning party remains liable after assignment unless expressly released", "high"),
    ("assignment", "Merger or acquisition of either party triggers assignment review provisions", "medium"),

    # === SUBCONTRACTING ===
    ("subcontracting", "Customer must approve all subcontractors in writing", "medium"),
    ("subcontracting", "Vendor remains fully liable for all subcontractor acts and omissions", "high"),
    ("subcontracting", "Subcontractors must meet the same security and compliance standards as the vendor", "high"),
    ("subcontracting", "Customer may request replacement of any subcontractor for reasonable cause", "medium"),
    ("subcontracting", "Vendor must maintain a current list of approved subcontractors available to the customer", "low"),
    ("subcontracting", "Subcontracting must not relieve the vendor of any obligations under the contract", "high"),

    # === NON-COMPETE ===
    ("non_compete", "Non-compete duration must not exceed 12 months post-termination", "high"),
    ("non_compete", "Non-compete geographic scope must be reasonably limited to the service territory", "high"),
    ("non_compete", "Non-compete must be supported by adequate consideration", "medium"),
    ("non_compete", "Non-compete must not restrict solicitation of customers with whom no business relationship existed", "medium"),
    ("non_compete", "Non-compete must be narrowly scoped to the specific business of the counterparty", "medium"),

    # === NON-SOLICITATION ===
    ("non_solicitation", "Non-solicitation of employees must not exceed 12 months post-termination", "medium"),
    ("non_solicitation", "Non-solicitation must not apply to general public job postings or hiring through search firms", "low"),
    ("non_solicitation", "Non-solicitation of customers must be limited to active prospects from the last 12 months", "medium"),
    ("non_solicitation", "Mutual non-solicitation is preferred over one-sided restrictions", "medium"),
    ("non_solicitation", "Non-solicitation must expressly exclude employees who respond to public advertisements", "low"),

    # === ENTIRE AGREEMENT ===
    ("entire_agreement", "Entire agreement clause must state it supersedes all prior negotiations and agreements", "low"),
    ("entire_agreement", "Entire agreement clause must include all exhibits, schedules, and attachments", "low"),
    ("entire_agreement", "The contract must expressly state that no other representations or warranties exist beyond those stated", "medium"),
    ("entire_agreement", "Entire agreement clause must preserve the validity of separate confidentiality or DPA agreements", "medium"),

    # === AMENDMENTS ===
    ("amendments", "Amendments must be in writing and signed by both parties", "high"),
    ("amendments", "No amendment is binding unless expressly referencing the clause being amended", "medium"),
    ("amendments", "Waiver of any term must not constitute waiver of any subsequent breach", "low"),
    ("amendments", "Course of dealing or performance must not override written terms", "medium"),

    # === PUBLICITY & MARKETING ===
    ("publicity", "No press release or public announcement mentioning the other party without prior written approval", "medium"),
    ("publicity", "Neither party may use the other party's trademarks without a separate license agreement", "medium"),
    ("publicity", "Customer case studies and references require express written consent", "medium"),
    ("publicity", "Marketing materials referencing the customer must comply with the customer's brand guidelines", "low"),

    # === NOTICES ===
    ("notices", "Notices must be in writing and delivered by confirmed delivery methods", "low"),
    ("notices", "Notice to either party must be sent to the designated representatives listed in the contract", "low"),
    ("notices", "Each party must update their notice address within 5 business days of any change", "low"),
    ("notices", "Email notice alone is insufficient for formal communications without confirmed receipt", "medium"),
    ("notices", "Deemed receipt rules must specify fixed timeframes for each delivery method", "low"),

    # === EXPORT CONTROL & SANCTIONS ===
    ("export_control", "Services must not be provided to sanctioned countries or entities", "high"),
    ("export_control", "Both parties must maintain export control compliance programs", "high"),
    ("export_control", "The vendor must not use restricted or denied parties in providing services", "high"),
    ("export_control", "Software and technical data exports must comply with EAR and ITAR regulations", "high"),
    ("export_control", "Each party must screen the other against OFAC sanctions lists before onboarding", "high"),
    ("export_control", "Export control and sanctions compliance obligations must survive termination", "high"),

    # === THIRD-PARTY BENEFICIARIES ===
    ("third_party", "No third-party beneficiaries are intended under this contract", "low"),
    ("third_party", "Third-party rights under the Contracts (Rights of Third Parties) Act 1999 must be expressly excluded", "medium"),
    ("third_party", "Affiliates of either party may be expressly named as third-party beneficiaries where intended", "low"),
    ("third_party", "Subcontractors must not acquire third-party beneficiary rights against the customer", "medium"),

    # === WAIVER ===
    ("waiver", "Waiver of any breach must not constitute waiver of any subsequent or different breach", "low"),
    ("waiver", "Any waiver must be in writing and signed by the waiving party", "medium"),
    ("waiver", "Failure to enforce any term must not be deemed a waiver of the right to enforce it later", "low"),
    ("waiver", "Waiver of rights must not extend beyond the specific instance waived", "low"),

    # === SEVERABILITY ===
    ("severability", "Invalid or unenforceable provisions must be modified to the minimum extent necessary to make them enforceable", "medium"),
    ("severability", "Severability clause must state that remaining provisions continue in full force and effect", "low"),
    ("severability", "If a provision cannot be modified, the parties must negotiate a replacement provision", "medium"),

    # === SURVIVAL ===
    ("survival", "Survival clause must list all provisions that survive termination", "high"),
    ("survival", "Confidentiality obligations must survive for at least 3 years", "high"),
    ("survival", "Indemnification obligations must survive for at least 12 months post-termination", "high"),
    ("survival", "Payment obligations must survive termination indefinitely until satisfied", "high"),
    ("survival", "Audit rights must survive for at least 2 years post-termination", "medium"),
    ("survival", "Insurance obligations must survive until all claims are resolved", "medium"),
    ("survival", "Limitation of liability must survive termination", "high"),
    ("survival", "Governing law and dispute resolution provisions must survive termination", "high"),

    # === INDEPENDENT CONTRACTOR ===
    ("independent_contractor", "The vendor is an independent contractor, not an employee or agent", "medium"),
    ("independent_contractor", "Each party is solely responsible for its own employee taxes, benefits, and compliance", "high"),
    ("independent_contractor", "Neither party has authority to bind the other party contractually", "medium"),
    ("independent_contractor", "Independent contractor language must expressly exclude joint employer status", "high"),
    ("independent_contractor", "No partnership, joint venture, or fiduciary relationship is created", "medium"),

    # === COUNTERPARTS & SIGNATURES ===
    ("counterparts", "The contract may be executed in counterparts with the same effect as a single document", "low"),
    ("counterparts", "Electronic signatures must be valid and enforceable under the ESIGN Act and eIDAS Regulation", "medium"),
    ("counterparts", "Facsimile, scanned, or electronic signatures are deemed original signatures", "low"),
    ("counterparts", "Each counterpart must be considered an original and together constitute one agreement", "low"),

    # === FURTHER ASSURANCES ===
    ("further_assurances", "Each party must execute additional documents reasonably necessary to effect the agreement", "low"),
    ("further_assurances", "Both parties must cooperate in good faith to perfect intellectual property rights", "medium"),

    # === TIME IS OF THE ESSENCE ===
    ("time_essence", "Time is of the essence for all performance deadlines stated in the contract", "medium"),
    ("time_essence", "Time is of the essence clauses must not apply to force majeure delayed obligations", "medium"),

    # === CUMULATIVE REMEDIES ===
    ("cumulative_remedies", "All remedies provided in the contract are cumulative and not exclusive of any other remedies", "medium"),
    ("cumulative_remedies", "Exercise of one remedy must not preclude exercise of any other remedy", "low"),
    ("cumulative_remedies", "Remedies under the contract are in addition to remedies available at law or equity", "low"),

    # === LEGAL FEES ===
    ("legal_fees", "The prevailing party in any dispute is entitled to recover reasonable attorneys fees and costs", "medium"),
    ("legal_fees", "Legal fees recovery must cover all stages of dispute resolution including arbitration and appeals", "medium"),
    ("legal_fees", "Legal fees clause must be mutual and apply equally to both parties", "high"),

    # === SET-OFF RIGHTS ===
    ("set_off", "Set-off rights must be mutual and available to both parties", "medium"),
    ("set_off", "Set-off must not be limited to amounts due under the same contract", "medium"),
    ("set_off", "Set-off rights must not be waived by accepting partial payment", "low"),

    # === DELIVERY & ACCEPTANCE ===
    ("delivery", "Delivery terms must follow Incoterms where applicable", "medium"),
    ("delivery", "Acceptance testing period must be at least 30 calendar days", "medium"),
    ("delivery", "Acceptance criteria must be objective and measurable", "high"),
    ("delivery", "Rejection of deliverables must include specific reasons and a cure period", "medium"),
    ("delivery", "Multiple acceptance testing rounds are permitted if initial testing fails", "medium"),
    ("delivery", "Deemed acceptance must not occur without the customer's affirmative written acceptance", "high"),

    # === TRAINING ===
    ("training", "Training must be provided at no additional cost during the implementation phase", "medium"),
    ("training", "Training materials must be provided in electronic format for future reference", "low"),
    ("training", "Train-the-trainer sessions must be available upon request", "low"),
    ("training", "Training must be delivered by qualified personnel with subject matter expertise", "medium"),

    # === SUPPORT ===
    ("support", "Technical support must be available 24/7/365 for critical issues", "high"),
    ("support", "Support requests must be tracked in a ticketing system with unique reference numbers", "medium"),
    ("support", "Customer must have a designated support account manager", "low"),
    ("support", "Support must be provided in the customer's primary language", "medium"),
    ("support", "Knowledge base and self-service portal must be available without additional charge", "low"),

    # === DISASTER RECOVERY & BUSINESS CONTINUITY ===
    ("disaster_recovery", "Vendor must maintain a documented disaster recovery plan tested at least annually", "high"),
    ("disaster_recovery", "Recovery time objective (RTO) must not exceed 4 hours for critical systems", "high"),
    ("disaster_recovery", "Recovery point objective (RPO) must not exceed 1 hour for critical data", "high"),
    ("disaster_recovery", "DR test results must be shared with the customer upon request", "medium"),
    ("disaster_recovery", "Business continuity plan must cover alternative work arrangements for personnel", "medium"),
    ("disaster_recovery", "Offsite backups must be geographically separated from primary data centers", "high"),
    ("disaster_recovery", "Backups must be encrypted both in transit and at rest", "high"),

    # === TRANSITION ASSISTANCE ===
    ("transition", "Vendor must provide transition assistance upon termination or expiration", "medium"),
    ("transition", "Transition period must be at least 90 days at no additional cost", "medium"),
    ("transition", "Transition assistance must include data export in industry-standard format", "high"),
    ("transition", "Vendor must reasonably cooperate with the successor vendor during transition", "medium"),
    ("transition", "Transition services may be provided at cost if not included in final contract period", "low"),

    # === RECORDS RETENTION ===
    ("records_retention", "Vendor must maintain complete and accurate records of all services performed", "medium"),
    ("records_retention", "Records must be retained for the longer of 7 years or applicable statutory periods", "high"),
    ("records_retention", "Records must be provided to the customer within 10 business days of request", "medium"),
    ("records_retention", "Records must be stored in a manner that prevents unauthorized alteration", "medium"),
    ("records_retention", "Upon termination, records must be transferred to the customer in electronic format", "high"),

    # === SANCTIONS & RESTRICTED PARTIES ===
    ("sanctions", "Neither party nor its affiliates may be on the OFAC SDN list or equivalent", "high"),
    ("sanctions", "Services must not be provided in or to Crimea, Cuba, Iran, North Korea, or Syria", "high"),
    ("sanctions", "Each party must have sanctions screening procedures for all personnel involved", "high"),
    ("sanctions", "Violation of sanctions must be immediately reported and constitutes material breach", "high"),

    # === DIVERSITY & SUBCONTRACTING GOALS ===
    ("diversity", "Vendor must make reasonable efforts to utilize diverse suppliers and subcontractors", "medium"),
    ("diversity", "Vendor must report diversity spend annually upon customer request", "low"),
    ("diversity", "Supplier diversity reporting must follow the customer's standard format", "low"),

    # === DATA SECURITY ===
    ("data_security", "All data in transit must be encrypted using TLS 1.2 or higher", "high"),
    ("data_security", "All data at rest must be encrypted using AES-256 or equivalent", "high"),
    ("data_security", "Multi-factor authentication must be required for all system access", "high"),
    ("data_security", "Access controls must follow the principle of least privilege", "high"),
    ("data_security", "Security incidents must be reported within 24 hours of discovery", "high"),
    ("data_security", "Penetration testing must be conducted at least annually by an independent third party", "high"),
    ("data_security", "Vulnerability scanning must be performed at least monthly", "medium"),
    ("data_security", "Security patches must be applied within 30 days of release for critical vulnerabilities", "high"),
    ("data_security", "User access must be reviewed and certified at least quarterly", "medium"),
    ("data_security", "Terminated employee access must be revoked within 24 hours", "high"),
    ("data_security", "Logging and monitoring must cover all system access and administrative actions", "high"),
    ("data_security", "Logs must be retained for at least 12 months and be tamper-proof", "medium"),
    ("data_security", "Customers must have the right to request security attestations and certifications", "medium"),
    ("data_security", "ISO 27001 certification or equivalent must be maintained", "high"),
    ("data_security", "SOC 2 Type II audit must be performed annually with report available to customers", "high"),

    # === COMPLIANCE CERTIFICATIONS ===
    ("compliance", "Vendor must maintain PCI DSS compliance if handling payment card data", "high"),
    ("compliance", "Vendor must comply with HIPAA if handling protected health information", "high"),
    ("compliance", "Vendor must maintain FedRAMP authorization if servicing US federal agencies", "high"),
    ("compliance", "Vendor must maintain applicable SOC certifications and provide reports", "high"),
    ("compliance", "Vendor must notify the customer of any change or loss of certification", "medium"),
    ("compliance", "Compliance with state-specific privacy laws (CCPA, CPA, VCDPA) must be maintained", "high"),

    # === RIGHT TO USE DELIVERABLES ===
    ("right_to_use", "Customer must have a perpetual, irrevocable right to use all deliverables", "high"),
    ("right_to_use", "Right to use must survive termination for cause", "high"),
    ("right_to_use", "Customer may modify deliverables for internal business purposes", "medium"),
    ("right_to_use", "Right to use must extend to the customer's affiliates and contractors", "medium"),

    # === BENCHMARKS ===
    ("benchmarks", "Vendor may not use the customer's name in benchmarks or case studies without consent", "medium"),
    ("benchmarks", "Benchmark results must be anonymized if used in public materials", "medium"),
    ("benchmarks", "Customer must have the right to review and approve benchmark methodologies", "low"),

    # === PRICING ===
    ("pricing", "All pricing must be in the currency stated and fixed for the initial term", "medium"),
    ("pricing", "Price increases must be capped at the lesser of CPI or 5% annually", "medium"),
    ("pricing", "Most favored customer pricing must apply to all subsequent contracts", "medium"),
    ("pricing", "Pricing must include all taxes, duties, and fees unless expressly excluded", "medium"),
    ("pricing", "Implementation and onboarding costs must be separately stated from recurring fees", "low"),
    ("pricing", "Early termination fees must be reasonable and proportionate to actual costs", "medium"),
    ("pricing", "One-time fees must not be charged for standard reports already in the system", "low"),

    # === SCOPE MANAGEMENT ===
    ("scope", "Changes in scope must be documented in a written change order signed by both parties", "high"),
    ("scope", "Change orders must include impact on timeline, cost, and resources", "medium"),
    ("scope", "Either party may request changes, but no work may proceed without an approved change order", "high"),
    ("scope", "Disagreements over scope must be escalated through the dispute resolution process", "medium"),
    ("scope", "Out-of-scope work must not proceed without a fully executed change order", "high"),
]


async def seed_guidelines(session: AsyncSession):
    from app.db.models import CorporateGuideline

    result = await session.execute(
        text("SELECT guideline_type, standard_text FROM corporate_guidelines")
    )
    existing = set((row[0], row[1]) for row in result.fetchall())

    new_count = 0
    for gtype, text_content, risk in GUIDELINES:
        if (gtype, text_content) in existing:
            continue
        session.add(
            CorporateGuideline(
                tenant_id="default",
                guideline_type=gtype,
                standard_text=text_content,
                risk_level=risk,
            )
        )
        new_count += 1

    if new_count:
        await session.commit()
        print(f"Seeded {new_count} new corporate guidelines")
    else:
        print("All corporate guidelines already up to date")
